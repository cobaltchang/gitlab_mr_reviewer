"""
主 CLI 應用程式測試
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from src.main import cli, init_app


@pytest.fixture
def runner():
    """建立 Click CLI 測試 runner"""
    return CliRunner()


@pytest.fixture
def mock_init_app():
    """Mock init_app 函數"""
    with patch('src.main.init_app') as mock:
        yield mock


class TestCLI:
    """CLI 命令測試"""
    
    def test_cli_help(self, runner):
        """測試 CLI help"""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'GitLab MR Reviewer' in result.output
    
    def test_cli_version(self, runner):
        """測試 CLI version"""
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert '1.0.0' in result.output


class TestScanCommand:
    """scan 命令測試"""
    
    @patch('src.main.init_app')
    @patch('src.main.mr_scanner')
    @patch('src.main.config')
    @patch('src.main.clone_manager')
    @patch('src.main.logger')
    def test_scan_dry_run(self, mock_logger, mock_clone_manager, mock_config, mock_scanner, mock_init, runner):
        """測試 scan --dry-run"""
        mock_config.projects = ['group/project']
        
        mock_mr = Mock()
        mock_mr.project_name = 'group/project'
        mock_mr.iid = 42
        mock_mr.title = 'Test MR'
        
        mock_result = Mock()
        mock_result.merge_requests = [mock_mr]
        mock_result.error = None
        mock_result.project = 'group/project'
        
        mock_scanner.scan.return_value = [mock_result]
        
        result = runner.invoke(cli, ['scan', '--dry-run'])
        
        assert result.exit_code == 0
        assert '試執行模式' in result.output
        assert 'group/project#42' in result.output
    
    @patch('src.main.init_app')
    @patch('src.main.mr_scanner')
    @patch('src.main.config')
    @patch('src.main.clone_manager')
    @patch('src.main.logger')
    def test_scan_creates_clones(self, mock_logger, mock_clone_manager, mock_config, mock_scanner, mock_init, runner):
        """測試 scan 建立 clone"""
        mock_config.projects = ['group/project']
        
        mock_mr = Mock()
        mock_mr.project_name = 'group/project'
        mock_mr.iid = 42
        mock_mr.title = 'Test MR'
        
        mock_result = Mock()
        mock_result.merge_requests = [mock_mr]
        mock_result.error = None
        mock_result.project = 'group/project'
        
        mock_scanner.scan.return_value = [mock_result]
        mock_clone_manager.create_clone.return_value = '/path/to/clone'
        
        result = runner.invoke(cli, ['scan'])
        
        assert result.exit_code == 0
        mock_clone_manager.create_clone.assert_called_once_with(mock_mr)


class TestListClonesCommand:
    """list-clones 命令測試"""
    
    @patch('src.main.init_app')
    @patch('src.main.clone_manager')
    @patch('src.main.logger')
    def test_list_clones_empty(self, mock_logger, mock_clone_manager, mock_init, runner):
        """測試列出空的 clone 列表"""
        mock_clone_manager.list_clones.return_value = {}
        
        result = runner.invoke(cli, ['list-clones'])
        
        assert result.exit_code == 0
        assert '沒有 clone' in result.output
    
    @patch('src.main.init_app')
    @patch('src.main.clone_manager')
    @patch('src.main.logger')
    def test_list_clones_with_clones(self, mock_logger, mock_clone_manager, mock_init, runner):
        """測試列出 clone"""
        mock_clone_manager.list_clones.return_value = {
            'group/project': [42, 123]
        }
        mock_clone_manager.get_clone_path.return_value = '/path/to/clone'
        
        result = runner.invoke(cli, ['list-clones'])
        
        assert result.exit_code == 0
        assert 'group/project' in result.output
        assert '#42' in result.output


class TestCleanCloneCommand:
    """clean-clone 命令測試"""
    
    @patch('src.main.init_app')
    @patch('src.main.clone_manager')
    @patch('src.main.logger')
    def test_clean_clone_success(self, mock_logger, mock_clone_manager, mock_init, runner):
        """測試成功刪除 clone"""
        mock_clone_manager.get_clone_path.return_value = '/path/to/clone'
        mock_clone_manager.delete_clone.return_value = True
        
        result = runner.invoke(cli, ['clean-clone', '--iid', '42', '--project', 'group/project'])
        
        assert result.exit_code == 0
        assert 'Clone 已刪除' in result.output
    
    @patch('src.main.init_app')
    @patch('src.main.clone_manager')
    @patch('src.main.logger')
    def test_clean_clone_not_exists(self, mock_logger, mock_clone_manager, mock_init, runner):
        """測試刪除不存在的 clone"""
        mock_clone_manager.get_clone_path.return_value = None
        
        result = runner.invoke(cli, ['clean-clone', '--iid', '42', '--project', 'group/project'])
        
        assert result.exit_code == 1
        assert 'Clone 不存在' in result.output


class TestBackwardCompatibility:
    """向後相容性測試"""
    
    @patch('src.main.init_app')
    @patch('src.main.clone_manager')
    @patch('src.main.logger')
    def test_list_worktrees_deprecated(self, mock_logger, mock_clone_manager, mock_init, runner):
        """測試 list-worktrees 已棄用警告"""
        mock_clone_manager.list_clones.return_value = {}
        
        result = runner.invoke(cli, ['list-worktrees'])
        
        # 應該顯示棄用警告
        assert '已棄用' in result.output or '警告' in result.output
