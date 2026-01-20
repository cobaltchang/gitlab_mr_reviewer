"""
測試 CLI scan 處理 ScanResult.error 與 create_worktree 拋例外的情形
"""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from src.main import cli


@pytest.fixture
def cli_runner():
    return CliRunner()


def test_scan_handles_scanresult_error(monkeypatch, cli_runner):
    def fake_init():
        import src.main as main
        main.logger = Mock()
        main.config = SimpleNamespace(projects=["group/proj"])
        main.mr_scanner = SimpleNamespace()
        main.mr_scanner.scan = lambda projects, exclude_wip, exclude_draft: [SimpleNamespace(project="group/proj", merge_requests=[], error="api failed")]
        main.worktree_manager = SimpleNamespace()

    monkeypatch.setattr('src.main.init_app', fake_init)

    result = cli_runner.invoke(cli, ["scan"])
    assert result.exit_code == 0
    assert "✗ group/proj: api failed" in result.output


def test_scan_create_worktree_exception(monkeypatch, cli_runner):
    def fake_init():
        import src.main as main
        main.logger = Mock()
        main.config = SimpleNamespace(projects=["group/proj"])
        main.mr_scanner = SimpleNamespace()
        mr = SimpleNamespace(project_name="group/proj", iid=99, title="t", source_branch="f", target_branch="m")
        main.mr_scanner.scan = lambda projects, exclude_wip, exclude_draft: [SimpleNamespace(project="group/proj", merge_requests=[mr], error=None)]
        wm = Mock()
        wm.create_worktree.side_effect = Exception('create failed')
        main.worktree_manager = wm

    monkeypatch.setattr('src.main.init_app', fake_init)

    result = cli_runner.invoke(cli, ["scan"])
    assert result.exit_code == 0
    assert "✗ group/proj#99" in result.output
