"""
測試 WorktreeManager._has_local_changes 對 .mr_info.json 的過濾行為
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

from src.worktree.manager import WorktreeManager


def test_has_local_changes_ignores_mr_info(tmp_path):
    repo_path = Path(tmp_path) / "repo"
    repo_path.mkdir()

    # 模擬 subprocess.run 回傳只有 .mr_info.json 的變更
    mock_result = MagicMock()
    mock_result.stdout = " M .mr_info.json\n"
    mock_result.returncode = 0

    with patch('subprocess.run', return_value=mock_result):
        has_changes = WorktreeManager._has_local_changes(repo_path)

    # 因為只有 .mr_info.json，應該視為沒有有意義的本地修改
    assert has_changes is False
