"""
補充測試以達到 100% 覆蓋率
"""
import json
import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch, MagicMock

import pytest
from click.testing import CliRunner

from src.clone.manager import CloneManager
from src.config import Config
from src.gitlab_.models import MRInfo
from src.main import cli
from src.state.manager import StateManager
from src.utils.exceptions import GitError, CloneError


@pytest.fixture
def temp_dir():
    """建立臨時目錄"""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp, ignore_errors=True)


@pytest.fixture
def mock_config(temp_dir):
    """建立模擬設定"""
    config = Mock(spec=Config)
    config.reviews_path = temp_dir
    config.gitlab_url = "https://gitlab.example.com/"
    config.state_dir = temp_dir
    config.db_path = f"{temp_dir}/db.sqlite"
    return config


@pytest.fixture
def mock_state_manager(temp_dir):
    """建立模擬狀態管理器"""
    return StateManager(db_path=f"{temp_dir}/db.sqlite")


@pytest.fixture
def sample_mr_info():
    """建立範例 MR 資訊"""
    return MRInfo(
        id=1,
        iid=42,
        project_id=10,
        project_name="group/project",
        title="Test MR",
        description="Test",
        source_branch="feature",
        target_branch="main",
        state="opened",
        author="test",
        web_url="https://gitlab.example.com/group/project/-/merge_requests/42",
        created_at="2024-01-01",
        updated_at="2024-01-01",
        draft=False,
        work_in_progress=False
    )


class TestCloneManagerExceptionPaths:
    """測試 CloneManager 的異常路徑"""
    
    def test_create_clone_git_error_cleanup(self, mock_config, mock_state_manager, sample_mr_info, temp_dir):
        """測試 GitError 導致的清理路徑"""
        manager = CloneManager(mock_config, mock_state_manager)
        
        # 先建立 clone_path 目錄以便測試清理邏輯
        clone_path = Path(temp_dir) / "group" / "project" / "42"
        clone_path.mkdir(parents=True, exist_ok=True)

        # 用 side_effect 包裝 shutil.rmtree：第一次呼叫不刪除（模擬刪除失敗），第二次呼叫執行真實刪除
        real_rmtree = shutil.rmtree
        call_state = {"count": 0}

        def fake_rmtree(path, ignore_errors=False):
            call_state["count"] += 1
            if call_state["count"] == 1:
                # 模擬第一次刪除未成功（目錄仍存在）
                return
            # 第二次及以後執行真實刪除
            return real_rmtree(path, ignore_errors=ignore_errors)

        # Mock _run_git_command 拋出 GitError
        with patch('shutil.rmtree', side_effect=fake_rmtree):
            with patch.object(manager, '_run_git_command', side_effect=GitError("git clone failed")):
                with pytest.raises(CloneError, match="建立 clone 失敗"):
                    manager.create_clone(sample_mr_info)
        
        # 驗證清理發生（目錄應被刪除）
        assert not clone_path.exists()
    
    def test_create_clone_general_exception_cleanup(self, mock_config, mock_state_manager, sample_mr_info, temp_dir):
        """測試一般異常導致的清理路徑"""
        manager = CloneManager(mock_config, mock_state_manager)
        
        # 先建立 clone_path 目錄以便測試清理邏輯
        clone_path = Path(temp_dir) / "group" / "project" / "42"
        clone_path.mkdir(parents=True, exist_ok=True)

        # 用 side_effect 包裝 shutil.rmtree：第一次呼叫不刪除（模擬刪除失敗），第二次呼叫執行真實刪除
        real_rmtree = shutil.rmtree
        call_state = {"count": 0}

        def fake_rmtree(path, ignore_errors=False):
            call_state["count"] += 1
            if call_state["count"] == 1:
                # 模擬第一次刪除未成功（目錄仍存在）
                return
            # 第二次及以後執行真實刪除
            return real_rmtree(path, ignore_errors=ignore_errors)

        # Mock _run_git_command 拋出普通 Exception
        with patch('shutil.rmtree', side_effect=fake_rmtree):
            with patch.object(manager, '_run_git_command', side_effect=Exception("unknown error")):
                with pytest.raises(CloneError, match="建立 clone 失敗"):
                    manager.create_clone(sample_mr_info)
        
        # 驗證清理發生（目錄應被刪除）
        assert not clone_path.exists()
    
    def test_delete_clone_exception_returns_false(self, mock_config, mock_state_manager, sample_mr_info, temp_dir):
        """測試刪除 clone 時的異常處理"""
        manager = CloneManager(mock_config, mock_state_manager)
        
        # 建立 clone 路徑
        clone_path = Path(temp_dir) / "group" / "project" / "42"
        clone_path.mkdir(parents=True, exist_ok=True)
        
        # Mock shutil.rmtree 拋出異常
        with patch('shutil.rmtree', side_effect=OSError("permission denied")):
            result = manager.delete_clone(sample_mr_info)
            assert result == False
    
    def test_list_clones_nested_structure(self, mock_config, mock_state_manager, temp_dir):
        """測試 list_clones 的雙層結構路徑"""
        manager = CloneManager(mock_config, mock_state_manager)
        
        # 建立雙層結構: reviews/group/project/123
        nested_path = Path(temp_dir) / "group" / "project" / "123"
        nested_path.mkdir(parents=True, exist_ok=True)
        
        result = manager.list_clones()
        assert "group/project" in result
        assert 123 in result["group/project"]
    
    def test_list_clones_single_layer_structure(self, mock_config, mock_state_manager, temp_dir):
        """測試 list_clones 的單層結構路徑"""
        manager = CloneManager(mock_config, mock_state_manager)
        
        # 建立單層結構: reviews/project/123 和 reviews/project/456 (同一專案多個 MR)
        project_path = Path(temp_dir) / "simple-project"
        (project_path / "456").mkdir(parents=True, exist_ok=True)
        (project_path / "789").mkdir(parents=True, exist_ok=True)
        
        result = manager.list_clones()
        assert "simple-project" in result
        assert 456 in result["simple-project"]
        assert 789 in result["simple-project"]
    
    def test_list_clones_no_reviews_path(self, mock_config, mock_state_manager, temp_dir):
        """測試 list_clones 當 reviews_path 不存在時返回空字典 (line 149)"""
        # 使用一個不存在的路徑
        mock_config.reviews_path = str(Path(temp_dir) / "non-existent")
        manager = CloneManager(mock_config, mock_state_manager)
        
        result = manager.list_clones()
        assert result == {}
    
    def test_save_mr_metadata_success(self, mock_config, mock_state_manager, sample_mr_info, temp_dir):
        """測試 _save_mr_metadata 成功寫入 (line 203)"""
        manager = CloneManager(mock_config, mock_state_manager)
        
        clone_path = Path(temp_dir) / "test"
        clone_path.mkdir(parents=True, exist_ok=True)
        
        # 呼叫私有方法
        manager._save_mr_metadata(sample_mr_info, clone_path)
        
        # 驗證檔案存在
        metadata_file = clone_path / ".mr_info.json"
        assert metadata_file.exists()
        
        # 驗證內容
        with open(metadata_file) as f:
            data = json.load(f)
            assert data["iid"] == 42
            assert data["project_name"] == "group/project"


class TestMainExceptionPaths:
    """測試 main.py 的異常路徑"""
    
    def test_scan_general_exception(self, monkeypatch):
        """測試 scan 命令的異常處理 (line 131 with logger)"""
        def fake_init():
            import src.main as main
            # 确保 logger 存在以触发 line 131
            main.logger = Mock()
            main.mr_scanner = Mock()
            main.mr_scanner.scan.side_effect = Exception("scan failed")
        
        monkeypatch.setattr('src.main.init_app', fake_init)
        
        runner = CliRunner()
        result = runner.invoke(cli, ["scan"])
        assert result.exit_code == 1
        assert "錯誤" in result.output
    
    def test_list_clones_exception(self, monkeypatch):
        """測試 list-clones 命令的異常處理"""
        def fake_init():
            import src.main as main
            main.logger = Mock()
            main.clone_manager = Mock()
            main.clone_manager.list_clones.side_effect = Exception("list failed")
        
        monkeypatch.setattr('src.main.init_app', fake_init)
        
        runner = CliRunner()
        result = runner.invoke(cli, ["list-clones"])
        assert result.exit_code == 1
        assert "錯誤" in result.output
    
    def test_clean_clone_delete_failure(self, monkeypatch):
        """測試 clean-clone 刪除失敗的情況"""
        def fake_init():
            import src.main as main
            main.logger = Mock()
            main.config = Mock()
            main.gitlab_client = Mock()
            
            mr_info = MagicMock()
            mr_info.project_name = "test/proj"
            mr_info.iid = 99
            
            main.gitlab_client.get_mr_details.return_value = mr_info
            main.clone_manager = Mock()
            main.clone_manager.delete_clone.return_value = False  # 刪除失敗
        
        monkeypatch.setattr('src.main.init_app', fake_init)
        
        runner = CliRunner()
        result = runner.invoke(cli, ["clean-clone", "--iid", "99", "--project", "test/proj"])
        assert result.exit_code == 1
        assert "刪除失敗" in result.output
    
    def test_clean_clone_exception(self, monkeypatch):
        """測試 clean-clone 命令中 get_clone_path 拋出異常"""
        def fake_init():
            import src.main as main
            main.logger = Mock()
            main.clone_manager = Mock()
            # 讓 get_clone_path 拋出異常
            main.clone_manager.get_clone_path.side_effect = Exception("path error")
        
        monkeypatch.setattr('src.main.init_app', fake_init)
        
        runner = CliRunner()
        result = runner.invoke(cli, ["clean-clone", "--iid", "99", "--project", "test/proj"])
        # 當拋出異常時，會被 except 捕獲並顯示錯誤資訊
        assert result.exit_code == 1
        assert "錯誤" in result.output
    


class TestCloneManagerGetRepoUrl:
    """測試 CloneManager._get_repo_url 方法"""
    
    def test_get_repo_url_with_gitlab_repo_base(self, mock_config, mock_state_manager, sample_mr_info):
        """測試使用 gitlab_repo_base 配置 (line 203)"""
        # 添加 gitlab_repo_base 属性
        mock_config.gitlab_repo_base = "git@custom-gitlab.com:"
        manager = CloneManager(mock_config, mock_state_manager)
        
        url = manager._get_repo_url(sample_mr_info)
        assert url == "git@custom-gitlab.com:group/project.git"
    
    def test_get_repo_url_with_http(self, mock_config, mock_state_manager, sample_mr_info):
        """測試使用 http:// 的 GitLab URL"""
        mock_config.gitlab_url = "http://gitlab.example.com/"
        manager = CloneManager(mock_config, mock_state_manager)
        
        url = manager._get_repo_url(sample_mr_info)
        assert url == "git@gitlab.example.com:group/project.git"
    
    def test_get_repo_url_without_protocol(self, mock_config, mock_state_manager, sample_mr_info):
        """測試沒有協議前綴的 GitLab URL"""
        mock_config.gitlab_url = "gitlab.example.com"
        manager = CloneManager(mock_config, mock_state_manager)
        
        url = manager._get_repo_url(sample_mr_info)
        assert url == "git@gitlab.example.com:group/project.git"
