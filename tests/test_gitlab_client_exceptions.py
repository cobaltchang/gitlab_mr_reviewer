"""
測試 GitLabClient 在不同方法遇到例外時會拋出 GitLabError
"""

from unittest.mock import Mock, patch
import pytest

from src.gitlab_.client import GitLabClient
from src.utils.exceptions import GitLabError


def test_get_merge_requests_raises_gitlaberror():
    with patch("src.gitlab_.client.gitlab.Gitlab") as mock_gitlab:
        mock_gl = Mock()
        mock_gitlab.return_value = mock_gl

        mock_project = Mock()
        mock_project.mergerequests.list.side_effect = Exception("boom")
        mock_gl.projects.get.return_value = mock_project

        client = GitLabClient("https://gitlab.example.com", "token")

        with pytest.raises(GitLabError):
            client.get_merge_requests("group/proj")


def test_get_mr_details_raises_gitlaberror():
    with patch("src.gitlab_.client.gitlab.Gitlab") as mock_gitlab:
        mock_gl = Mock()
        mock_gitlab.return_value = mock_gl

        mock_project = Mock()
        mock_project.mergerequests.get.side_effect = Exception("boom2")
        mock_gl.projects.get.return_value = mock_project

        client = GitLabClient("https://gitlab.example.com", "token")

        with pytest.raises(GitLabError):
            client.get_mr_details("group/proj", 1)
