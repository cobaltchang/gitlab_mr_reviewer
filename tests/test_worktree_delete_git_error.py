"""
測試 delete_worktree 在 git 命令失敗時回傳 False
"""

from unittest.mock import patch

from src.worktree.manager import WorktreeManager
from src.utils.exceptions import GitError
from src.config import Config
from src.state.manager import StateManager
from src.gitlab_.models import MRInfo


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
        id=5, iid=20, project_id=1, project_name="group/project",
        title="t", description="", author="a",
        source_branch="f", target_branch="m", web_url="",
        created_at="", updated_at="", state="opened",
        draft=False, work_in_progress=False
    )


def test_delete_worktree_git_error(tmp_path):
    config = _make_config(tmp_path)
    state_manager = StateManager(storage_type="json", state_dir=str(tmp_path / 'state'))
    wm = WorktreeManager(config=config, state_manager=state_manager)

    mr = _make_mr()

    # 建立目錄以讓存在檢查通過
    path = wm._get_worktree_path(mr)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.mkdir(parents=True, exist_ok=True)

    with patch.object(WorktreeManager, '_run_git_command', side_effect=GitError('git fail')):
        result = wm.delete_worktree(mr)
        assert result is False
