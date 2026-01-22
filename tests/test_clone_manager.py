"""
CloneManager 測試
"""
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.clone.manager import CloneManager
from src.config import Config
from src.gitlab_.models import MRInfo
from src.state.manager import StateManager
from src.utils.exceptions import CloneError, GitError


@pytest.fixture
def config(tmp_path):
    """建立測試用 Config"""
    reviews_path = tmp_path / "reviews"
    reviews_path.mkdir()
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    
    return Config(
        gitlab_url="https://gitlab.example.com",
        gitlab_token="test-token",
        projects=["group/project"],
        reviews_path=str(reviews_path),
        state_dir=str(state_dir),
        db_path=str(state_dir / "db.sqlite"),
    )


@pytest.fixture
def state_manager(tmp_path):
    """建立測試用 StateManager"""
    state_dir = tmp_path / "state"
    state_dir.mkdir(exist_ok=True)
    return StateManager(db_path=str(state_dir / "db.sqlite"))


@pytest.fixture
def mr_info():
    """建立測試用 MRInfo"""
    return MRInfo(
        id=123,
        project_id=456,
        project_name="group/project",
        iid=42,
        title="Test MR",
        description="Test description",
        state="opened",
        author="testuser",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-02T00:00:00Z",
        source_branch="feature/test",
        target_branch="main",
        web_url="https://gitlab.example.com/group/project/-/merge_requests/42",
        draft=False,
        work_in_progress=False,
    )


@pytest.fixture
def clone_manager(config, state_manager):
    """建立測試用 CloneManager"""
    return CloneManager(config, state_manager)


class TestCloneManager:
    """CloneManager 測試"""
    
    def test_init(self, clone_manager, config, state_manager):
        """測試初始化"""
        assert clone_manager.config == config
        assert clone_manager.state_manager == state_manager
    
    def test_get_clone_path(self, clone_manager, mr_info, config):
        """測試取得 clone 路徑"""
        expected = Path(config.reviews_path).expanduser() / "group/project" / "42"
        actual = clone_manager._get_clone_path(mr_info)
        assert actual == expected
    
    def test_get_repo_url_from_gitlab_url(self, clone_manager, mr_info):
        """測試從 gitlab_url 推導 repo URL"""
        url = clone_manager._get_repo_url(mr_info)
        assert url == "git@gitlab.example.com:group/project.git"
    
    @patch.object(CloneManager, '_run_git_command')
    def test_create_clone_success(self, mock_git, clone_manager, mr_info, config):
        """測試成功建立 clone"""
        clone_path = clone_manager.create_clone(mr_info)
        
        expected_path = Path(config.reviews_path).expanduser() / "group/project" / "42"
        assert clone_path == expected_path
        
        # 驗證 git clone + fetch + checkout 被呼叫
        assert mock_git.call_count == 3

        # 第一個呼叫應為 clone，使用 target_branch
        first_call_args = mock_git.call_args_list[0][0][0]
        assert first_call_args[0] == 'git'
        assert first_call_args[1] == 'clone'
        assert '-b' in first_call_args
        assert mr_info.target_branch in first_call_args
        assert '--single-branch' in first_call_args
    
    @patch.object(CloneManager, '_run_git_command')
    def test_create_clone_removes_existing_dir(self, mock_git, clone_manager, mr_info, config):
        """測試建立 clone 時會先刪除已存在的目錄"""
        clone_path = Path(config.reviews_path).expanduser() / "group/project" / "42"
        clone_path.mkdir(parents=True)
        (clone_path / "dummy.txt").write_text("test")
        
        result = clone_manager.create_clone(mr_info)
        
        # 應該呼叫 git clone + fetch + checkout（舊目錄已被刪除）
        assert mock_git.call_count == 3
    
    @patch.object(CloneManager, '_run_git_command')
    def test_create_clone_saves_metadata(self, mock_git, clone_manager, mr_info, config):
        """測試建立 clone 後會保存元資料"""
        clone_path = clone_manager.create_clone(mr_info)
        
        metadata_file = clone_path / '.mr_info.json'
        assert metadata_file.exists()
        
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        assert metadata['mr_id'] == 123
        assert metadata['iid'] == 42
        assert metadata['source_branch'] == 'feature/test'
    
    @patch.object(CloneManager, '_run_git_command')
    def test_create_clone_git_error(self, mock_git, clone_manager, mr_info):
        """測試 git clone 失敗時拋出 CloneError"""
        mock_git.side_effect = GitError("clone failed")
        
        with pytest.raises(CloneError) as exc:
            clone_manager.create_clone(mr_info)
        
        assert "clone failed" in str(exc.value)
    
    def test_delete_clone_success(self, clone_manager, mr_info, config):
        """測試成功刪除 clone"""
        clone_path = Path(config.reviews_path).expanduser() / "group/project" / "42"
        clone_path.mkdir(parents=True)
        (clone_path / "dummy.txt").write_text("test")
        
        result = clone_manager.delete_clone(mr_info)
        
        assert result is True
        assert not clone_path.exists()
    
    def test_delete_clone_not_exists(self, clone_manager, mr_info):
        """測試刪除不存在的 clone"""
        result = clone_manager.delete_clone(mr_info)
        assert result is False
    
    def test_list_clones_empty(self, clone_manager):
        """測試列出 clone（空目錄）"""
        result = clone_manager.list_clones()
        assert result == {}
    
    def test_list_clones_with_clones(self, clone_manager, config):
        """測試列出 clone"""
        reviews_path = Path(config.reviews_path).expanduser()
        
        # 建立一些 clone 目錄
        (reviews_path / "group/project" / "42").mkdir(parents=True)
        (reviews_path / "group/project" / "123").mkdir(parents=True)
        (reviews_path / "other/repo" / "7").mkdir(parents=True)
        
        result = clone_manager.list_clones()
        
        assert "group/project" in result
        assert set(result["group/project"]) == {42, 123}
        assert "other/repo" in result
        assert result["other/repo"] == [7]
    
    def test_get_clone_path_exists(self, clone_manager, config):
        """測試取得存在的 clone 路徑"""
        clone_path = Path(config.reviews_path).expanduser() / "group/project" / "42"
        clone_path.mkdir(parents=True)
        
        result = clone_manager.get_clone_path("group/project", 42)
        assert result == clone_path
    
    def test_get_clone_path_not_exists(self, clone_manager):
        """測試取得不存在的 clone 路徑"""
        result = clone_manager.get_clone_path("group/project", 999)
        assert result is None


class TestCloneManagerGitCommand:
    """測試 git 命令執行"""
    
    def test_run_git_command_success(self):
        """測試成功執行 git 命令"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="output", stderr="")
            
            CloneManager._run_git_command(['git', 'status'])
            
            mock_run.assert_called_once()
    
    def test_run_git_command_failure(self):
        """測試 git 命令失敗"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="", stderr="error message")
            
            with pytest.raises(GitError) as exc:
                CloneManager._run_git_command(['git', 'clone', 'bad-url'])
            
            assert "error message" in str(exc.value)
    
    def test_run_git_command_exception(self):
        """測試 git 命令拋出異常"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("subprocess error")
            
            with pytest.raises(GitError) as exc:
                CloneManager._run_git_command(['git', 'status'])
            
            assert "subprocess error" in str(exc.value)
