"""
自訂異常類定義
"""


class ConfigError(Exception):
    """設定錯誤"""
    pass


class GitLabError(Exception):
    """GitLab API 錯誤"""
    pass


class CloneError(Exception):
    """Clone 操作錯誤"""
    pass


# 保留別名以維持向後相容
WorktreeError = CloneError


class StateError(Exception):
    """狀態管理錯誤"""
    pass


class GitError(Exception):
    """Git 操作錯誤"""
    pass

