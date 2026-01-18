"""
狀態管理器
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Optional

from src.logger import logger
from src.state.models import MRState
from src.utils.exceptions import StateError


class StateManager:
    """狀態持久化管理"""
    
    def __init__(self, storage_type: str = "sqlite", db_path: str = None, state_dir: str = "./state"):
        """
        初始化狀態管理器
        
        Args:
            storage_type: 存儲類型 ("sqlite" 或 "json")
            db_path: SQLite 資料庫路徑
            state_dir: 狀態儲存目錄
        """
        self.storage_type = storage_type
        self.db_path = db_path
        self.state_dir = Path(state_dir).expanduser()
        
        # 建立狀態目錄
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        if storage_type == "sqlite":
            self._init_sqlite()
        elif storage_type == "json":
            self._init_json()
    
    def _init_sqlite(self):
        """初始化 SQLite 資料庫"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 建立 merge_requests 表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS merge_requests (
                    id INTEGER PRIMARY KEY,
                    mr_id INTEGER,
                    project_slug TEXT,
                    iid INTEGER,
                    state TEXT,
                    head_commit_sha TEXT,
                    saved_at TEXT
                )
            """)
            
            # 建立 scan_history 表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scan_history (
                    id INTEGER PRIMARY KEY,
                    scan_time TEXT,
                    project TEXT,
                    mr_count INTEGER,
                    success BOOLEAN
                )
            """)
            
            conn.commit()
            conn.close()
            
            logger.info(f"初始化 SQLite 資料庫: {self.db_path}")
        except Exception as e:
            logger.error(f"初始化 SQLite 資料庫失敗: {e}")
            raise StateError(f"初始化 SQLite 資料庫失敗: {e}")
    
    def _init_json(self):
        """初始化 JSON 存儲"""
        self.mr_state_file = self.state_dir / "mr_states.json"
        self.scan_history_file = self.state_dir / "scan_history.json"
        
        # 建立初始檔案
        if not self.mr_state_file.exists():
            with open(self.mr_state_file, "w") as f:
                json.dump([], f)
        
        if not self.scan_history_file.exists():
            with open(self.scan_history_file, "w") as f:
                json.dump([], f)
        
        logger.info(f"初始化 JSON 儲存: {self.state_dir}")
    
    def save_mr_state(self, mr_state: MRState):
        """
        保存 MR 狀態
        
        Args:
            mr_state: MR 狀態物件
        """
        try:
            if self.storage_type == "sqlite":
                self._save_mr_state_sqlite(mr_state)
            else:
                self._save_mr_state_json(mr_state)
        except Exception as e:
            logger.error(f"保存 MR 狀態失敗: {e}")
            raise StateError(f"保存 MR 狀態失敗: {e}")
    
    def _save_mr_state_sqlite(self, mr_state: MRState):
        """保存 MR 狀態到 SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO merge_requests 
            (mr_id, project_slug, iid, state, head_commit_sha, saved_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            mr_state.mr_id,
            mr_state.project_slug,
            mr_state.iid,
            mr_state.state,
            mr_state.head_commit_sha,
            mr_state.saved_at,
        ))
        
        conn.commit()
        conn.close()
    
    def _save_mr_state_json(self, mr_state: MRState):
        """保存 MR 狀態到 JSON"""
        with open(self.mr_state_file, "r") as f:
            states = json.load(f)
        
        # 查找並更新或新增
        for i, state in enumerate(states):
            if state["mr_id"] == mr_state.mr_id and state["project_slug"] == mr_state.project_slug:
                states[i] = mr_state.__dict__
                break
        else:
            states.append(mr_state.__dict__)
        
        with open(self.mr_state_file, "w") as f:
            json.dump(states, f, indent=2)
    
    def get_mr_state(self, mr_id: int, project_slug: str) -> Optional[MRState]:
        """
        取得 MR 狀態
        
        Args:
            mr_id: MR ID
            project_slug: 專案路徑
            
        Returns:
            MRState 物件或 None
        """
        try:
            if self.storage_type == "sqlite":
                return self._get_mr_state_sqlite(mr_id, project_slug)
            else:
                return self._get_mr_state_json(mr_id, project_slug)
        except Exception as e:
            logger.error(f"取得 MR 狀態失敗: {e}")
            raise StateError(f"取得 MR 狀態失敗: {e}")
    
    def _get_mr_state_sqlite(self, mr_id: int, project_slug: str) -> Optional[MRState]:
        """從 SQLite 取得 MR"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT mr_id, project_slug, iid, state, head_commit_sha, saved_at
            FROM merge_requests
            WHERE mr_id = ? AND project_slug = ?
        """, (mr_id, project_slug))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return MRState(
                mr_id=row[0],
                project_slug=row[1],
                iid=row[2],
                state=row[3],
                head_commit_sha=row[4],
                saved_at=row[5],
            )
        return None
    
    def _get_mr_state_json(self, mr_id: int, project_slug: str) -> Optional[MRState]:
        """從 JSON 取得 MR"""
        with open(self.mr_state_file, "r") as f:
            states = json.load(f)
        
        for state in states:
            if state["mr_id"] == mr_id and state["project_slug"] == project_slug:
                return MRState(**state)
        
        return None
    
    def get_all_mr_states(self) -> List[MRState]:
        """
        取得所有 MR 狀態
        
        Returns:
            MRState 列表
        """
        try:
            if self.storage_type == "sqlite":
                return self._get_all_mr_states_sqlite()
            else:
                return self._get_all_mr_states_json()
        except Exception as e:
            logger.error(f"取得所有 MR 狀態失敗: {e}")
            raise StateError(f"取得所有 MR 狀態失敗: {e}")
    
    def _get_all_mr_states_sqlite(self) -> List[MRState]:
        """從 SQLite 取得所有 MR"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT mr_id, project_slug, iid, state, head_commit_sha, saved_at
            FROM merge_requests
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            MRState(
                mr_id=row[0],
                project_slug=row[1],
                iid=row[2],
                state=row[3],
                head_commit_sha=row[4],
                saved_at=row[5],
            ) for row in rows
        ]
    
    def _get_all_mr_states_json(self) -> List[MRState]:
        """從 JSON 取得所有 MR"""
        with open(self.mr_state_file, "r") as f:
            states = json.load(f)
        
        return [MRState(**state) for state in states]
    
    def delete_mr_state(self, mr_id: int, project_slug: str):
        """
        刪除 MR 狀態
        
        Args:
            mr_id: MR ID
            project_slug: 專案路徑
        """
        try:
            if self.storage_type == "sqlite":
                self._delete_mr_state_sqlite(mr_id, project_slug)
            else:
                self._delete_mr_state_json(mr_id, project_slug)
        except Exception as e:
            logger.error(f"刪除 MR 狀態失敗: {e}")
            raise StateError(f"刪除 MR 狀態失敗: {e}")
    
    def _delete_mr_state_sqlite(self, mr_id: int, project_slug: str):
        """從 SQLite 刪除 MR"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM merge_requests
            WHERE mr_id = ? AND project_slug = ?
        """, (mr_id, project_slug))
        
        conn.commit()
        conn.close()
    
    def _delete_mr_state_json(self, mr_id: int, project_slug: str):
        """從 JSON 刪除 MR"""
        with open(self.mr_state_file, "r") as f:
            states = json.load(f)
        
        states = [
            state for state in states
            if not (state["mr_id"] == mr_id and state["project_slug"] == project_slug)
        ]
        
        with open(self.mr_state_file, "w") as f:
            json.dump(states, f, indent=2)
