"""
自訂異常類定義
"""


class ConfigError(Exception):
    """設定錯誤"""
    pass


class GitLabError(Exception):
    """GitLab API 錯誤"""
    pass


class WorktreeError(Exception):
    """Worktree 操作錯誤"""
    pass


class StateError(Exception):
    """狀態管理錯誤"""
    pass


class GitError(Exception):
    """Git 操作錯誤"""
    pass

