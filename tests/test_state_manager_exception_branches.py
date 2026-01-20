"""
測試 StateManager 的 get/get_all/delete 在內部方法拋例外時的 StateError 行為
"""

from unittest.mock import patch
import pytest

from src.state.manager import StateManager
from src.utils.exceptions import StateError


def test_get_mr_state_handles_internal_exception(tmp_path):
    manager = StateManager(storage_type="json", state_dir=str(tmp_path / 'state'))

    with patch.object(manager, '_get_mr_state_json', side_effect=Exception('boom')):
        with pytest.raises(StateError):
            manager.get_mr_state(1, 'g/p')


def test_get_all_mr_states_handles_internal_exception(tmp_path):
    manager = StateManager(storage_type="json", state_dir=str(tmp_path / 'state'))

    with patch.object(manager, '_get_all_mr_states_json', side_effect=Exception('boom')):
        with pytest.raises(StateError):
            manager.get_all_mr_states()


def test_delete_mr_state_handles_internal_exception(tmp_path):
    manager = StateManager(storage_type="json", state_dir=str(tmp_path / 'state'))

    with patch.object(manager, '_delete_mr_state_json', side_effect=Exception('boom')):
        with pytest.raises(StateError):
            manager.delete_mr_state(1, 'g/p')
