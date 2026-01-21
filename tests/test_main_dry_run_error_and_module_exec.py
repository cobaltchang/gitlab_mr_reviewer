"""
測試 scan --dry-run 在遇到 ScanResult.error 時的輸出，以及以 __main__ 執行 module 封裝
"""

import runpy
import sys
import pytest
from types import SimpleNamespace
from unittest.mock import Mock

from click.testing import CliRunner
from src.main import cli


@pytest.fixture
def cli_runner():
    return CliRunner()


def test_scan_dry_run_shows_errors(monkeypatch, cli_runner):
    def fake_init():
        import src.main as main
        main.logger = Mock()
        main.config = SimpleNamespace(projects=["group/proj"])
        main.mr_scanner = SimpleNamespace()
        main.mr_scanner.scan = lambda projects, exclude_wip, exclude_draft: [SimpleNamespace(project="group/proj", merge_requests=[], error="api fail")]
        main.worktree_manager = SimpleNamespace()

    monkeypatch.setattr('src.main.init_app', fake_init)

    result = cli_runner.invoke(cli, ["scan", "--dry-run"])
    assert result.exit_code == 0
    assert "✗ group/proj: api fail" in result.output


def test_run_module_main_executes_cli(monkeypatch, capsys):
    # simulate running as a script with --version
    monkeypatch.setattr(sys, 'argv', ['src.main', '--version'])
    # run_module will call cli() and may raise SystemExit
    with pytest.raises(SystemExit) as se:
        runpy.run_module('src.main', run_name='__main__')
    # version option should exit with code 0
    assert se.value.code == 0
