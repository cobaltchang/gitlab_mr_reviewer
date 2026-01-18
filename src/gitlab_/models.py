"""
GitLab API 資料模型
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Change:
    """MR 的檔案變更"""
    old_path: str
    new_path: str
    new_file: bool
    deleted_file: bool
    renamed_file: bool


@dataclass
class Commit:
    """MR 的提交"""
    id: str
    short_id: str
    title: str
    message: str
    author_name: str
    author_email: str
    created_at: str


@dataclass
class MRInfo:
    """Merge Request 訊息"""
    id: int
    project_id: int
    project_name: str
    iid: int
    title: str
    description: str
    state: str  # opened, closed, merged, etc.
    author: str
    created_at: str
    updated_at: str
    source_branch: str
    target_branch: str
    web_url: str
    draft: bool
    work_in_progress: bool
