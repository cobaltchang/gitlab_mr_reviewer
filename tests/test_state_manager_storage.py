"""
測試 StateManager 的 JSON 和 SQLite 存取行為
"""

import json
from pathlib import Path

from src.state.manager import StateManager
from src.state.models import MRState


def test_json_storage_save_get_delete(tmp_path):
    state_dir = tmp_path / "state"
    manager = StateManager(storage_type="json", state_dir=str(state_dir))

    mr_state = MRState(mr_id=42, project_slug="group/proj", iid=7, state="opened", head_commit_sha="abc", saved_at="now")

    manager.save_mr_state(mr_state)

    loaded = manager.get_mr_state(42, "group/proj")
    assert loaded is not None
    assert loaded.mr_id == 42

    all_states = manager.get_all_mr_states()
    assert any(s.mr_id == 42 for s in all_states)

    manager.delete_mr_state(42, "group/proj")
    assert manager.get_mr_state(42, "group/proj") is None


def test_sqlite_storage_save_get_delete(tmp_path):
    db_path = tmp_path / "state" / "state.db"
    manager = StateManager(storage_type="sqlite", db_path=str(db_path), state_dir=str(tmp_path / "state"))

    mr_state = MRState(mr_id=100, project_slug="group/proj2", iid=8, state="opened", head_commit_sha="def", saved_at="now")

    manager.save_mr_state(mr_state)

    loaded = manager.get_mr_state(100, "group/proj2")
    assert loaded is not None
    assert loaded.mr_id == 100

    all_states = manager.get_all_mr_states()
    assert any(s.mr_id == 100 for s in all_states)

    manager.delete_mr_state(100, "group/proj2")
    assert manager.get_mr_state(100, "group/proj2") is None


def test_json_update_existing(tmp_path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    mr_file = state_dir / "mr_states.json"
    # prepopulate with one state
    mr_file.write_text('[{"mr_id":200, "project_slug":"g/p", "iid":5, "state":"opened", "head_commit_sha":"x", "saved_at":"old"}]')

    manager = StateManager(storage_type="json", state_dir=str(state_dir))

    from src.state.models import MRState
    mr_state = MRState(mr_id=200, project_slug='g/p', iid=5, state='closed', head_commit_sha='y', saved_at='now')
    manager.save_mr_state(mr_state)

    loaded = manager.get_mr_state(200, 'g/p')
    assert loaded is not None
    assert loaded.state == 'closed'
