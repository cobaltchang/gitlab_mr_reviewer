"""
測試 WorktreeManager 在 Git 錯誤發生時的行為
"""

import pytest
from unittest.mock import patch

from src.worktree.manager import WorktreeManager
from src.utils.exceptions import WorktreeError, GitError
from src.gitlab_.models import MRInfo
from src.config import Config
from src.state.manager import StateManager


def _make_config(tmp_path):
    return Config(
        gitlab_url="https://gitlab.com",
        gitlab_token="token",
        projects=["group/project"],
        reviews_path=str(tmp_path / "reviews"),
        state_dir=str(tmp_path / "state"),
        db_path=str(tmp_path / "state" / "state.db"),
    )


def _make_mr():
    return MRInfo(
        id=1,
        iid=11,
        project_id=1,
        project_name="group/project",
        title="Fail MR",
        description="",
        author="a",
        source_branch="feature/x",
        target_branch="main",
        web_url="",
        created_at="",
        updated_at="",
        state="opened",
        draft=False,
        work_in_progress=False,
    )


def test_create_worktree_git_fetch_error(tmp_path):
    config = _make_config(tmp_path)
    state_manager = StateManager(storage_type="json", state_dir=str(tmp_path / "state"))
    wm = WorktreeManager(config=config, state_manager=state_manager)

    mr = _make_mr()

    # 模擬 _run_git_command 在 fetch 時拋出 GitError
    with patch.object(WorktreeManager, '_run_git_command', side_effect=GitError("git failed")):
        with pytest.raises(WorktreeError):
            wm.create_worktree(mr)
