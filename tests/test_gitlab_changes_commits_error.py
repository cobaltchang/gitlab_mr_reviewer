"""
測試 GitLabClient.get_mr_changes / get_mr_commits 在底層 API 失敗時會拋出 GitLabError
"""

from unittest.mock import Mock, patch
import pytest

from src.gitlab_.client import GitLabClient
from src.utils.exceptions import GitLabError


def test_get_mr_changes_api_error():
    with patch("src.gitlab_.client.gitlab.Gitlab") as mock_gitlab:
        mock_gl = Mock()
        mock_gitlab.return_value = mock_gl

        mock_mr = Mock()
        mock_mr.changes.side_effect = Exception('boom changes')

        mock_project = Mock()
        mock_project.mergerequests.get.return_value = mock_mr
        mock_gl.projects.get.return_value = mock_project

        client = GitLabClient("https://gitlab.example.com", "token")

        with pytest.raises(GitLabError):
            client.get_mr_changes('group/proj', 1)


def test_get_mr_commits_api_error():
    with patch("src.gitlab_.client.gitlab.Gitlab") as mock_gitlab:
        mock_gl = Mock()
        mock_gitlab.return_value = mock_gl

        mock_mr = Mock()
        mock_mr.commits.side_effect = Exception('boom commits')

        mock_project = Mock()
        mock_project.mergerequests.get.return_value = mock_mr
        mock_gl.projects.get.return_value = mock_project

        client = GitLabClient("https://gitlab.example.com", "token")

        with pytest.raises(GitLabError):
            client.get_mr_commits('group/proj', 1)
