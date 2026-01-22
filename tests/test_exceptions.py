"""
異常類測試
"""

import pytest

from src.utils.exceptions import (
    ConfigError,
    GitLabError,
    StateError,
    GitError,
)


class TestExceptions:
    """異常類的測試"""

    def test_config_error_is_exception(self):
        """ConfigError 是 Exception 的子類"""
        assert issubclass(ConfigError, Exception)

    def test_config_error_message(self):
        """ConfigError 可以保存訊息"""
        error = ConfigError("測試訊息")
        assert str(error) == "測試訊息"

    def test_gitlab_error_is_exception(self):
        """GitLabError 是 Exception 的子類"""
        assert issubclass(GitLabError, Exception)

    def test_gitlab_error_with_context(self):
        """GitLabError 可以帶上下文訊息"""
        error = GitLabError("API 呼叫失敗: 401 Unauthorized")
        assert "401" in str(error)

    def test_worktree_error(self):
        # WorktreeError removed; ensure CloneError exists instead
        from src.utils.exceptions import CloneError
        with pytest.raises(CloneError):
            raise CloneError("Clone 建立失敗")

    def test_state_error(self):
        """StateError 可以正確拋出"""
        with pytest.raises(StateError):
            raise StateError("狀態載入失敗")

    def test_git_error(self):
        """GitError 可以正確拋出"""
        with pytest.raises(GitError):
            raise GitError("Git 命令執行失敗")

    def test_exception_hierarchy(self):
        """所有異常類都是 Exception 的子類"""
        exceptions = [
            ConfigError,
            GitLabError,
            StateError,
            GitError,
        ]
        for exc in exceptions:
            assert issubclass(exc, Exception)
