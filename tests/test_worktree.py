"""
Worktree 管理模組測試
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
from src.worktree.manager import WorktreeManager


@pytest.fixture
def temp_dir():
    """建立臨時目錄"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def config(temp_dir):
    """建立測試 Config"""
    return Config(
        gitlab_url="https://gitlab.com",
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
def worktree_manager(config, state_manager):
    """建立 WorktreeManager 實例"""
    return WorktreeManager(config=config, state_manager=state_manager)


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
        web_url="https://gitlab.com/group/project/-/merge_requests/10",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-02T00:00:00Z",
        state="opened",
        draft=False,
        work_in_progress=False,
    )


class TestWorktreeManagerInit:
    """測試 WorktreeManager 初始化"""
    
    def test_worktree_manager_init(self, worktree_manager, config, state_manager):
        """測試初始化"""
        assert worktree_manager.config == config
        assert worktree_manager.state_manager == state_manager


class TestWorktreeManagerPath:
    """測試 Worktree 路徑操作"""
    
    def test_get_worktree_path(self, worktree_manager, mr_info, temp_dir):
        """測試取得 worktree 路徑"""
        expected_path = Path(temp_dir) / "reviews" / "project" / "10"
        actual_path = worktree_manager._get_worktree_path(mr_info)
        
        assert actual_path == expected_path
    
    def test_save_mr_metadata(self, worktree_manager, mr_info, temp_dir):
        """測試儲存 MR 元數據"""
        worktree_path = Path(temp_dir) / "worktree"
        worktree_path.mkdir(parents=True, exist_ok=True)
        
        worktree_manager._save_mr_metadata(mr_info, worktree_path)
        
        metadata_file = worktree_path / ".mr_info.json"
        assert metadata_file.exists()
        
        with open(metadata_file) as f:
            data = json.load(f)
        
        assert data["mr_id"] == 1
        assert data["iid"] == 10
        assert data["project_name"] == "project"
        assert data["title"] == "測試 MR"


class TestWorktreeManagerCreate:
    """測試 Worktree 建立操作"""
    
    @patch('src.worktree.manager.WorktreeManager._run_git_command')
    def test_create_worktree_success(self, mock_git, worktree_manager, mr_info, temp_dir):
        """測試成功建立 worktree"""
        result = worktree_manager.create_worktree(mr_info)
        
        # 檢查路徑
        expected_path = Path(temp_dir) / "reviews" / "project" / "10"
        assert result == expected_path
        
        # 檢查元數據檔案
        metadata_file = result / ".mr_info.json"
        assert metadata_file.exists()
        
        # 檢查 git 命令呼叫
        mock_git.assert_called_once()
        call_args = mock_git.call_args[0][0]
        assert call_args[0] == "git"
        assert call_args[1] == "worktree"
        assert call_args[2] == "add"
        assert call_args[3] == str(expected_path)
        assert call_args[4] == "origin/feature/test"
    
    @patch('src.worktree.manager.WorktreeManager._run_git_command')
    def test_create_worktree_already_exists(self, mock_git, worktree_manager, mr_info, temp_dir):
        """測試 worktree 已存在的情況"""
        # 預先建立 worktree 目錄
        worktree_path = Path(temp_dir) / "reviews" / "project" / "10"
        worktree_path.mkdir(parents=True, exist_ok=True)
        
        result = worktree_manager.create_worktree(mr_info)
        
        assert result == worktree_path
        # git 命令不應被呼叫（因為已存在）
        mock_git.assert_not_called()


class TestWorktreeManagerUpdate:
    """測試 Worktree 更新操作"""
    
    @patch('src.worktree.manager.WorktreeManager._run_git_command')
    @patch('src.worktree.manager.WorktreeManager._has_local_changes')
    @patch('src.worktree.manager.WorktreeManager._get_current_sha')
    def test_update_worktree_success(
        self, mock_sha, mock_changes, mock_git, worktree_manager, mr_info, temp_dir
    ):
        """測試成功更新 worktree"""
        # 設定 Mock
        mock_sha.return_value = "old_sha123"
        mock_changes.return_value = False
        
        # 預先建立 worktree
        worktree_path = Path(temp_dir) / "reviews" / "project" / "10"
        worktree_path.mkdir(parents=True, exist_ok=True)
        
        result = worktree_manager.update_worktree(mr_info)
        
        assert result is True
        # 應該呼叫 git pull
        assert mock_git.called
    
    @patch('src.worktree.manager.WorktreeManager._get_current_sha')
    def test_update_worktree_not_exists(self, mock_sha, worktree_manager, mr_info):
        """測試 worktree 不存在的情況"""
        result = worktree_manager.update_worktree(mr_info)
        
        assert result is False
        mock_sha.assert_not_called()
    
    @patch('src.worktree.manager.WorktreeManager._has_local_changes')
    @patch('src.worktree.manager.WorktreeManager._get_current_sha')
    def test_update_worktree_with_local_changes(
        self, mock_sha, mock_changes, worktree_manager, mr_info, temp_dir
    ):
        """測試 worktree 有本地修改的情況"""
        # 預先建立 worktree
        worktree_path = Path(temp_dir) / "reviews" / "project" / "10"
        worktree_path.mkdir(parents=True, exist_ok=True)
        
        # 設定 Mock
        mock_sha.return_value = "old_sha123"
        mock_changes.return_value = True
        
        result = worktree_manager.update_worktree(mr_info)
        
        assert result is False


class TestWorktreeManagerDelete:
    """測試 Worktree 刪除操作"""
    
    @patch('src.worktree.manager.WorktreeManager._run_git_command')
    def test_delete_worktree_success(self, mock_git, worktree_manager, mr_info, temp_dir):
        """測試成功刪除 worktree"""
        # 預先建立 worktree
        worktree_path = Path(temp_dir) / "reviews" / "project" / "10"
        worktree_path.mkdir(parents=True, exist_ok=True)
        
        result = worktree_manager.delete_worktree(mr_info)
        
        assert result is True
        assert not worktree_path.exists()
        # 應該呼叫 git worktree remove
        mock_git.assert_called_once()
    
    def test_delete_worktree_not_exists(self, worktree_manager, mr_info):
        """測試 worktree 不存在的情況"""
        result = worktree_manager.delete_worktree(mr_info)
        
        assert result is False


class TestWorktreeManagerHelpers:
    """測試輔助方法"""
    
    def test_get_current_sha(self, temp_dir):
        """測試取得當前 SHA"""
        # 建立模擬 Git 倉庫
        repo_path = Path(temp_dir) / "repo"
        repo_path.mkdir()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout="abc123def456\n",
                returncode=0
            )
            
            sha = WorktreeManager._get_current_sha(repo_path)
            
            assert sha == "abc123def456"
    
    def test_has_local_changes_no_changes(self, temp_dir):
        """測試檢查本地修改 - 無修改"""
        repo_path = Path(temp_dir) / "repo"
        repo_path.mkdir()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout="",
                returncode=0
            )
            
            has_changes = WorktreeManager._has_local_changes(repo_path)
            
            assert has_changes is False
    
    def test_has_local_changes_with_changes(self, temp_dir):
        """測試檢查本地修改 - 有修改"""
        repo_path = Path(temp_dir) / "repo"
        repo_path.mkdir()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout=" M file.py\n",
                returncode=0
            )
            
            has_changes = WorktreeManager._has_local_changes(repo_path)
            
            assert has_changes is True
    
    def test_run_git_command_success(self):
        """測試執行 Git 命令 - 成功"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout="success",
                returncode=0
            )
            
            # 應該不拋出異常
            WorktreeManager._run_git_command(["git", "status"])
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
                WorktreeManager._run_git_command(["git", "status"])
