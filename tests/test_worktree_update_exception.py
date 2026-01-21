import os
from pathlib import Path

from src.worktree.manager import WorktreeManager
from src.gitlab_.models import MRInfo
from src.config import Config
from src.state.manager import StateManager


def test_update_worktree_exception_returns_false(tmp_path, monkeypatch):
    reviews = tmp_path / "reviews"
    reviews.mkdir()

    # minimal config
    config = Config(
        gitlab_url="https://gitlab",
        gitlab_token="t",
        projects=["group/proj"],
        reviews_path=str(reviews),
        state_dir=str(tmp_path / "state"),
        db_path=str(tmp_path / "state" / "db.sqlite"),
    )

    # simple state manager stub
    state_manager = StateManager(str(tmp_path / "state"))

    manager = WorktreeManager(config, state_manager)

    mr = MRInfo(
        id=1,
        project_id=2,
        project_name="group/proj",
        iid=123,
        title="t",
        description="d",
        state="opened",
        author="a",
        created_at="now",
        updated_at="now",
        source_branch="feat",
        target_branch="main",
        web_url="u",
        draft=False,
        work_in_progress=False,
    )

    # Ensure worktree path exists so method proceeds
    wt = Path(config.reviews_path).expanduser() / mr.project_name / str(mr.iid)
    wt.parent.mkdir(parents=True, exist_ok=True)
    wt.mkdir(parents=True, exist_ok=True)

    # Force _get_current_sha to raise so the method hits the except and returns False
    def raise_exc(_):
        raise Exception("boom")

    monkeypatch.setattr(manager, "_get_current_sha", raise_exc)

    result = manager.update_worktree(mr)

    assert result is False
"""
測試 WorktreeManager.update_worktree 在 git 命令失敗時會回傳 False（例外分支）
"""

from unittest.mock import patch

from src.worktree.manager import WorktreeManager
from src.config import Config
from src.state.manager import StateManager
from src.gitlab_.models import MRInfo


def _make_config(tmp_path):
    return Config(
        gitlab_url="https://gitlab.example.com",
        gitlab_token="token",
        projects=["group/project"],
        reviews_path=str(tmp_path / "reviews"),
        state_dir=str(tmp_path / "state"),
        db_path=str(tmp_path / "state" / "state.db"),
    )


def test_update_worktree_handles_exception(tmp_path):
    config = _make_config(tmp_path)
    state_manager = StateManager(storage_type="json", state_dir=str(tmp_path / 'state'))
    wm = WorktreeManager(config=config, state_manager=state_manager)

    mr = MRInfo(
        id=1, iid=99, project_id=1, project_name="group/project",
        title="t", description="", author="a",
        source_branch="f", target_branch="main", web_url="",
        created_at="", updated_at="", state="opened",
        draft=False, work_in_progress=False
    )

    # create worktree path so update attempts to run
    p = wm._get_worktree_path(mr)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.mkdir(parents=True, exist_ok=True)

    with patch.object(WorktreeManager, '_run_git_command', side_effect=Exception('git fail')):
        result = wm.update_worktree(mr)
        assert result is False
