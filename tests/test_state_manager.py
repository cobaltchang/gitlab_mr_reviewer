"""
狀態管理測試
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from src.state.manager import StateManager
from src.state.models import MRState
from src.gitlab_.models import MRInfo


class TestStateManager:
    """狀態管理器的測試"""

    def test_state_manager_init_sqlite(self, tmp_path):
        """初始化 SQLite 狀態管理器"""
        db_path = tmp_path / "test.sqlite"
        state_dir = tmp_path / "state"
        
        manager = StateManager(
            storage_type="sqlite",
            db_path=str(db_path),
            state_dir=str(state_dir)
        )
        
        assert manager is not None
        assert state_dir.exists()

    def test_state_manager_init_json(self, tmp_path):
        """初始化 JSON 狀態管理器"""
        state_dir = tmp_path / "state"
        
        manager = StateManager(
            storage_type="json",
            state_dir=str(state_dir)
        )
        
        assert manager is not None
        assert state_dir.exists()

    def test_mr_state_creation(self):
        """建立 MRState"""
        mr_state = MRState(
            mr_id=1,
            project_slug="test/project",
            iid=100,
            state="opened",
            head_commit_sha="abc123"
        )
        
        assert mr_state.mr_id == 1
        assert mr_state.project_slug == "test/project"
        assert mr_state.iid == 100

    def test_mr_state_from_mr_info(self):
        """從 MRInfo 建立 MRState"""
        mr_info = MRInfo(
            id=1,
            project_id=10,
            project_name="test/project",
            iid=100,
            title="Test MR",
            description="",
            state="opened",
            author="test",
            created_at="2026-01-19",
            updated_at="2026-01-19",
            source_branch="feature",
            target_branch="main",
            web_url="",
            draft=False,
            work_in_progress=False
        )
        
        mr_state = MRState.from_mr_info(mr_info)
        
        assert mr_state.mr_id == 1
        assert mr_state.project_slug == "test/project"
        assert mr_state.iid == 100
        assert mr_state.state == "opened"
