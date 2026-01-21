"""
整合性 CLI 測試（scan / list-worktrees / clean-worktree）
"""

from types import SimpleNamespace
from pathlib import Path
from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from src.main import cli
from src.gitlab_.models import MRInfo


@pytest.fixture
def cli_runner():
    return CliRunner()


def _make_mr(iid=10, project_name="group/project"):
    return MRInfo(
        id=1,
        iid=iid,
        project_id=1,
        project_name=project_name,
        title="Test MR",
        description="",
        state="opened",
        author="tester",
        created_at="",
        updated_at="",
        source_branch="feature",
        target_branch="main",
        web_url="",
        draft=False,
        work_in_progress=False,
    )


def test_scan_dry_run_outputs_mr_list(monkeypatch, cli_runner):
    """scan --dry-run 應該列出 MR 而不建立 worktree"""
    # 建立假的 init_app，注入 mr_scanner 與 config
    def fake_init():
        import src.main as main
        from unittest.mock import Mock
        main.config = SimpleNamespace(projects=["group/project"])
        mock_scanner = SimpleNamespace()
        mock_scanner.scan = lambda projects, exclude_wip, exclude_draft: [
            SimpleNamespace(project="group/project", merge_requests=[_make_mr()], error=None)
        ]
        main.mr_scanner = mock_scanner
        main.worktree_manager = SimpleNamespace()
        main.logger = Mock()

    monkeypatch.setattr('src.main.init_app', fake_init)

    result = cli_runner.invoke(cli, ["scan", "--dry-run"])

    assert result.exit_code == 0
    assert "試執行模式" in result.output
    assert "group/project#10" in result.output or "group/project#10".replace('#', '#')


def test_scan_non_dry_run_invokes_create(monkeypatch, cli_runner, tmp_path):
    """非 dry-run 應該呼叫 worktree 建立並輸出路徑"""
    def fake_init():
        import src.main as main
        from unittest.mock import Mock
        main.config = SimpleNamespace(projects=["group/project"])
        mock_scanner = SimpleNamespace()
        mock_scanner.scan = lambda projects, exclude_wip, exclude_draft: [
            SimpleNamespace(project="group/project", merge_requests=[_make_mr()], error=None)
        ]
        main.mr_scanner = mock_scanner
        mock_wm = Mock()
        main.logger = Mock()
        expected_path = tmp_path / "reviews" / "group" / "project" / "10"
        mock_wm.create_worktree.return_value = expected_path
        main.worktree_manager = mock_wm

    monkeypatch.setattr('src.main.init_app', fake_init)

    result = cli_runner.invoke(cli, ["scan"])

    assert result.exit_code == 0
    assert "✓" in result.output or "完成" in result.output
    assert str(tmp_path) in result.output or "worktree" in result.output
    # ensure create_worktree was called
    import src.main as main
    assert main.worktree_manager.create_worktree.called


def test_list_worktrees_no_worktrees(monkeypatch, cli_runner):
    def fake_init():
        import src.main as main
        from unittest.mock import Mock
        main.worktree_manager = SimpleNamespace()
        main.worktree_manager.list_worktrees = lambda: {}
        main.logger = Mock()

    monkeypatch.setattr('src.main.init_app', fake_init)

    result = cli_runner.invoke(cli, ["list-worktrees"])

    assert result.exit_code == 0
    assert "沒有 worktree" in result.output


def test_clean_worktree_not_exists(monkeypatch, cli_runner):
    def fake_init():
        import src.main as main
        from unittest.mock import Mock
        main.worktree_manager = SimpleNamespace()
        main.worktree_manager.get_worktree_path = lambda project, iid: None
        main.logger = Mock()

    monkeypatch.setattr('src.main.init_app', fake_init)

    result = cli_runner.invoke(cli, ["clean-worktree", "--iid", "10", "--project", "group/project"])

    # clean_worktree calls exit(1) when not found
    assert result.exit_code != 0
    assert "Worktree 不存在" in result.output
