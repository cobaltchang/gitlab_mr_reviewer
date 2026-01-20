"""
測試 CLI clean-worktree 成功流程（init_app stub）
"""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from src.main import cli


@pytest.fixture
def cli_runner():
    return CliRunner()


def test_clean_worktree_success(monkeypatch, cli_runner):
    def fake_init():
        import src.main as main
        main.logger = Mock()
        wm = Mock()
        # get_worktree_path 回傳一個 path-like object
        wm.get_worktree_path.return_value = "/tmp/reviews/group/proj/10"
        wm.delete_worktree.return_value = True
        main.worktree_manager = wm

    monkeypatch.setattr('src.main.init_app', fake_init)

    result = cli_runner.invoke(cli, ["clean-worktree", "--iid", "10", "--project", "group/proj"])

    assert result.exit_code == 0
    assert "Worktree 已刪除" in result.output
