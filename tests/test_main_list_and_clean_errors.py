"""
測試 list_worktrees 有項目列出，以及 clean_worktree 刪除失敗與 init_app 拋例外情形
"""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from src.main import cli


@pytest.fixture
def cli_runner():
    return CliRunner()


def test_list_worktrees_with_entries(monkeypatch, cli_runner):
    def fake_init():
        import src.main as main
        main.logger = Mock()
        wm = SimpleNamespace()
        wm.list_worktrees = lambda: {"group/proj": [10, 11]}
        wm.get_worktree_path = lambda project, iid: f"/tmp/reviews/{project}/{iid}"
        main.worktree_manager = wm

    monkeypatch.setattr('src.main.init_app', fake_init)

    result = cli_runner.invoke(cli, ["list-worktrees"])
    assert result.exit_code == 0
    assert "group/proj:" in result.output
    assert "#10" in result.output
    assert "總計: 2 個 worktree" in result.output


def test_clean_worktree_delete_failure(monkeypatch, cli_runner):
    def fake_init():
        import src.main as main
        main.logger = Mock()
        wm = Mock()
        wm.get_worktree_path.return_value = "/tmp/reviews/group/proj/10"
        wm.delete_worktree.return_value = False
        main.worktree_manager = wm

    monkeypatch.setattr('src.main.init_app', fake_init)

    result = cli_runner.invoke(cli, ["clean-worktree", "--iid", "10", "--project", "group/proj"])
    assert result.exit_code != 0
    assert "✗ 刪除失敗" in result.output


def test_scan_init_app_exception(monkeypatch, cli_runner):
    def fake_init():
        raise Exception('init fail')

    monkeypatch.setattr('src.main.init_app', fake_init)

    result = cli_runner.invoke(cli, ["scan"])
    assert result.exit_code != 0
    assert "✗ 錯誤: init fail" in result.output


def test_list_worktrees_init_exception(monkeypatch, cli_runner):
    def fake_init():
        raise Exception('init fail list')

    monkeypatch.setattr('src.main.init_app', fake_init)

    result = cli_runner.invoke(cli, ["list-worktrees"])
    assert result.exit_code != 0
    assert "✗ 錯誤: init fail list" in result.output


def test_clean_worktree_init_exception(monkeypatch, cli_runner):
    def fake_init():
        raise Exception('init fail clean')

    monkeypatch.setattr('src.main.init_app', fake_init)

    result = cli_runner.invoke(cli, ["clean-worktree", "--iid", "1", "--project", "group/proj"])
    assert result.exit_code != 0
    assert "✗ 錯誤: init fail clean" in result.output
