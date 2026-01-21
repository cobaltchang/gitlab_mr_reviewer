"""
Clone 管理模組測試
"""

import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.config import Config
from src.gitlab_.models import MRInfo
from src.state.manager import StateManager
from src.clone.manager import CloneManager


@pytest.fixture
def temp_dir():
    """建立臨時目錄"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def config(temp_dir):
    """建立測試 Config"""
    return Config(
        gitlab_url="https://gitlab.example.com",
        gitlab_token="test_token",
        projects=["group/project"],
        reviews_path=str(temp_dir / "reviews"),
        state_dir=str(temp_dir / "state"),
        db_path=str(temp_dir / "state" / "state.db"),
    )


@pytest.fixture
def state_manager(config):
    """建立測試 StateManager"""
    # 建立必要的目錄
    Path(config.db_path).parent.mkdir(parents=True, exist_ok=True)
    return StateManager(db_path=config.db_path)


@pytest.fixture
def clone_manager(config, state_manager):
    """建立 CloneManager 實例"""
    return CloneManager(config=config, state_manager=state_manager)


@pytest.fixture
def mr_info():
    """建立測試 MRInfo"""
    return MRInfo(
        id=1,
        iid=10,
        project_id=1,
        project_name="project",
        title="測試 MR",
        description="測試描述",
        author="user@example.com",
        source_branch="feature/test",
        target_branch="main",
        web_url="https://gitlab.example.com/group/project/-/merge_requests/10",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-02T00:00:00Z",
        state="opened",
        draft=False,
        work_in_progress=False,
    )


class TestCloneManagerInit:
    """測試 CloneManager 初始化"""
    
    def test_clone_manager_init(self, clone_manager, config, state_manager):
        """測試初始化"""
        assert clone_manager.config == config
        assert clone_manager.state_manager == state_manager


class TestCloneManagerPath:
    """測試 Clone 路徑操作"""
    
    def test_get_clone_path(self, clone_manager, mr_info, temp_dir):
        """測試取得 clone 路徑"""
        expected_path = Path(temp_dir) / "reviews" / "project" / "10"
        actual_path = clone_manager._get_clone_path(mr_info)
        
        assert actual_path == expected_path
    
    def test_save_mr_metadata(self, clone_manager, mr_info, temp_dir):
        """測試儲存 MR 元數據"""
        clone_path = Path(temp_dir) / "clone"
        clone_path.mkdir(parents=True, exist_ok=True)
        
        clone_manager._save_mr_metadata(mr_info, clone_path)
        
        metadata_file = clone_path / ".mr_info.json"
        assert metadata_file.exists()
        
        with open(metadata_file) as f:
            data = json.load(f)
        
        assert data["mr_id"] == 1
        assert data["iid"] == 10
        assert data["project_name"] == "project"
        assert data["title"] == "測試 MR"


class TestCloneManagerCreate:
    """測試 Clone 建立操作"""
    
    @patch('src.clone.manager.CloneManager._run_git_command')
    def test_create_clone_success(self, mock_git, clone_manager, mr_info, temp_dir):
        """測試成功建立 clone"""
        result = clone_manager.create_clone(mr_info)
        
        # 檢查路徑
        expected_path = Path(temp_dir) / "reviews" / "project" / "10"
        assert result == expected_path
        
        # 檢查元數據檔案
        metadata_file = result / ".mr_info.json"
        assert metadata_file.exists()
        
        # 檢查 git 命令呼叫（應該有 3 次：clone + fetch + checkout）
        assert mock_git.call_count == 3
        
        # 檢查第一次呼叫（clone）
        first_call_args = mock_git.call_args_list[0][0][0]
        assert first_call_args[0] == "git"
        assert first_call_args[1] == "clone"
        assert first_call_args[2] == "-b"
        assert first_call_args[3] == "main"  # target_branch
        assert first_call_args[4] == "--single-branch"
        
        # 檢查第二次呼叫（fetch）
        second_call_args = mock_git.call_args_list[1][0][0]
        assert second_call_args[0] == "git"
        assert second_call_args[1] == "fetch"
        assert second_call_args[2] == "origin"
        assert f"refs/merge-requests/{mr_info.iid}/head" in second_call_args[3]
        
        # 檢查第三次呼叫（checkout）
        third_call_args = mock_git.call_args_list[2][0][0]
        assert third_call_args[0] == "git"
        assert third_call_args[1] == "checkout"
        assert third_call_args[2] == "FETCH_HEAD"
    
    @patch('src.clone.manager.CloneManager._run_git_command')
    @patch('shutil.rmtree')
    def test_create_clone_already_exists(self, mock_rmtree, mock_git, clone_manager, mr_info, temp_dir):
        """測試 clone 已存在的情況（會刪除後重建）"""
        # 預先建立 clone 目錄
        clone_path = Path(temp_dir) / "reviews" / "project" / "10"
        clone_path.mkdir(parents=True, exist_ok=True)
        
        result = clone_manager.create_clone(mr_info)
        
        # 應該先刪除舊目錄
        mock_rmtree.assert_called()
        
        # 應該重新建立
        assert result == clone_path
        # git 命令應該被呼叫（3 次）
        assert mock_git.call_count == 3
    
    @patch('src.clone.manager.CloneManager._run_git_command')
    def test_create_clone_git_clone_error(self, mock_git, clone_manager, mr_info, temp_dir):
        """測試 git clone 失敗時拋出 CloneError"""
        from src.utils.exceptions import GitError, CloneError
        
        # 模擬 git clone 失敗
        mock_git.side_effect = GitError("clone failed")
        
        with pytest.raises(CloneError):
            clone_manager.create_clone(mr_info)
    
    @patch('src.clone.manager.CloneManager._run_git_command')
    def test_create_clone_git_fetch_error(self, mock_git, clone_manager, mr_info, temp_dir):
        """測試 git fetch 失敗時拋出 CloneError"""
        from src.utils.exceptions import GitError, CloneError
        
        # 第一次成功（clone），第二次失敗（fetch）
        mock_git.side_effect = [None, GitError("fetch failed")]
        
        with pytest.raises(CloneError):
            clone_manager.create_clone(mr_info)
    
    @patch('src.clone.manager.CloneManager._run_git_command')
    def test_create_clone_git_checkout_error(self, mock_git, clone_manager, mr_info, temp_dir):
        """測試 git checkout 失敗時拋出 CloneError"""
        from src.utils.exceptions import GitError, CloneError
        
        # 前兩次成功（clone + fetch），第三次失敗（checkout）
        mock_git.side_effect = [None, None, GitError("checkout failed")]
        
        with pytest.raises(CloneError):
            clone_manager.create_clone(mr_info)


class TestCloneManagerDelete:
    """測試 Clone 刪除操作"""
    
    def test_delete_clone_success(self, clone_manager, mr_info, temp_dir):
        """測試成功刪除 clone"""
        # 預先建立 clone
        clone_path = Path(temp_dir) / "reviews" / "project" / "10"
        clone_path.mkdir(parents=True, exist_ok=True)
        
        result = clone_manager.delete_clone(mr_info)
        
        assert result is True
        assert not clone_path.exists()
    
    def test_delete_clone_not_exists(self, clone_manager, mr_info):
        """測試 clone 不存在的情況"""
        result = clone_manager.delete_clone(mr_info)
        
        assert result is False


class TestCloneManagerList:
    """測試 Clone 列表操作"""
    
    def test_list_clones_empty(self, clone_manager):
        """測試列出空的 clone 列表"""
        clones = clone_manager.list_clones()
        
        assert clones == {}
    
    def test_list_clones_with_data(self, clone_manager, temp_dir):
        """測試列出有資料的 clone 列表"""
        # 建立測試目錄結構
        reviews_path = Path(temp_dir) / "reviews"
        (reviews_path / "project1" / "10").mkdir(parents=True, exist_ok=True)
        (reviews_path / "project1" / "20").mkdir(parents=True, exist_ok=True)
        (reviews_path / "group" / "project2" / "30").mkdir(parents=True, exist_ok=True)
        
        clones = clone_manager.list_clones()
        
        assert "project1" in clones
        assert 10 in clones["project1"]
        assert 20 in clones["project1"]
        assert "group/project2" in clones
        assert 30 in clones["group/project2"]


class TestCloneManagerGetClonePath:
    """測試取得 Clone 路徑"""
    
    def test_get_clone_path_exists(self, clone_manager, temp_dir):
        """測試取得存在的 clone 路徑"""
        # 建立測試目錄
        clone_path = Path(temp_dir) / "reviews" / "project" / "10"
        clone_path.mkdir(parents=True, exist_ok=True)
        
        result = clone_manager.get_clone_path("project", 10)
        
        assert result == clone_path
    
    def test_get_clone_path_not_exists(self, clone_manager):
        """測試取得不存在的 clone 路徑"""
        result = clone_manager.get_clone_path("project", 999)
        
        assert result is None


class TestCloneManagerHelpers:
    """測試輔助方法"""
    
    def test_get_repo_url_with_repo_base(self, clone_manager, mr_info):
        """測試使用 gitlab_repo_base 取得 repo URL"""
        # 設定 gitlab_repo_base
        clone_manager.config.gitlab_repo_base = "git@gitlab.example.com:"
        
        url = clone_manager._get_repo_url(mr_info)
        
        assert url == "git@gitlab.example.com:project.git"
    
    def test_get_repo_url_from_gitlab_url(self, clone_manager, mr_info):
        """測試從 gitlab_url 推導 repo URL"""
        # 確保沒有 gitlab_repo_base
        if hasattr(clone_manager.config, 'gitlab_repo_base'):
            delattr(clone_manager.config, 'gitlab_repo_base')
        
        url = clone_manager._get_repo_url(mr_info)
        
        assert url == "git@gitlab.example.com:project.git"
    
    def test_run_git_command_success(self):
        """測試執行 Git 命令 - 成功"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout="success",
                returncode=0
            )
            
            # 應該不拋出異常
            CloneManager._run_git_command(["git", "status"])
            mock_run.assert_called_once()
    
    def test_run_git_command_failure(self):
        """測試執行 Git 命令 - 失敗"""
        from src.utils.exceptions import GitError
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stderr="fatal error",
                returncode=1
            )
            
            with pytest.raises(GitError):
                CloneManager._run_git_command(["git", "status"])


class TestWorktreeManagerAlias:
    """測試向後相容別名"""
    
    def test_worktree_manager_is_clone_manager(self):
        """測試 WorktreeManager 是 CloneManager 的別名"""
        from src.clone.manager import WorktreeManager
        
        assert WorktreeManager is CloneManager