"""
測試 StateManager 在初始化或保存時的錯誤處理路徑
"""

import sqlite3
from unittest.mock import patch
import pytest

from src.state.manager import StateManager
from src.utils.exceptions import StateError


def test_sqlite_init_failure(monkeypatch, tmp_path):
    # 模擬 sqlite3.connect 在初始化時拋出例外
    monkeypatch.setenv("PYTEST_RUNNING", "1")

    with patch('sqlite3.connect', side_effect=Exception('db fail')):
        with pytest.raises(StateError):
            StateManager(storage_type="sqlite", db_path=str(tmp_path / 'db.sqlite'), state_dir=str(tmp_path / 'state'))


def test_save_mr_state_propagates_stateerror(monkeypatch, tmp_path):
    manager = StateManager(storage_type="json", state_dir=str(tmp_path / 'state'))

    # 模擬內部方法拋出例外
    with patch.object(manager, '_save_mr_state_json', side_effect=Exception('io fail')):
        from src.state.models import MRState
        mr_state = MRState(mr_id=1, project_slug='g/p', iid=1, state='opened', head_commit_sha='x', saved_at='now')
        with pytest.raises(StateError):
            manager.save_mr_state(mr_state)
