"""
CLI 主應用程式測試
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from click.testing import CliRunner

from src.main import cli


@pytest.fixture
def cli_runner():
    """建立 CLI 測試 Runner"""
    return CliRunner()


class TestCLIVersionCommand:
    """測試版本命令"""
    
    def test_version(self, cli_runner):
        """測試 --version 選項"""
        result = cli_runner.invoke(cli, ["--version"])
        
        assert result.exit_code == 0
        assert "1.0.0" in result.output


class TestCLIScanCommand:
    """測試掃描命令"""
    
    @patch('src.main.Config')
    def test_scan_help(self, mock_config_class, cli_runner):
        """測試掃描命令幫助"""
        result = cli_runner.invoke(cli, ["scan", "--help"])
        
        assert result.exit_code == 0
        assert "掃描 GitLab 並建立或更新 Worktree" in result.output
        assert "--exclude-wip" in result.output
        assert "--exclude-draft" in result.output
        assert "--dry-run" in result.output


class TestCLIListCommand:
    """測試列表命令"""
    
    def test_list_help(self, cli_runner):
        """測試列表命令幫助"""
        result = cli_runner.invoke(cli, ["list-worktrees", "--help"])
        
        assert result.exit_code == 0
        assert "列出所有管理的 Worktree" in result.output


class TestCLICleanCommand:
    """測試清理命令"""
    
    def test_clean_help(self, cli_runner):
        """測試清理命令幫助"""
        result = cli_runner.invoke(cli, ["clean-worktree", "--help"])
        
        assert result.exit_code == 0
        assert "刪除指定的 Worktree" in result.output
        assert "--iid" in result.output
        assert "--project" in result.output


class TestCLIStructure:
    """測試 CLI 結構"""
    
    def test_scan_command_exists(self, cli_runner):
        """測試 scan 命令存在"""
        result = cli_runner.invoke(cli, ["--help"])
        assert "scan" in result.output
    
    def test_list_command_exists(self, cli_runner):
        """測試 list-worktrees 命令存在"""
        result = cli_runner.invoke(cli, ["--help"])
        assert "list-worktrees" in result.output
    
    def test_clean_command_exists(self, cli_runner):
        """測試 clean-worktree 命令存在"""
        result = cli_runner.invoke(cli, ["--help"])
        assert "clean-worktree" in result.output
