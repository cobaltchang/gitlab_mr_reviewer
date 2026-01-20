"""
測試 GitLabClient 取得 MR 變更與提交的映射
"""

from unittest.mock import Mock, patch

from src.gitlab_.client import GitLabClient
from src.gitlab_.models import Change, Commit


def test_get_mr_changes_maps_fields():
    with patch("src.gitlab_.client.gitlab.Gitlab") as mock_gitlab:
        mock_gl = Mock()
        mock_gitlab.return_value = mock_gl

        mock_change = {"old_path": "a.py", "new_path": "a.py", "new_file": False, "deleted_file": False, "renamed_file": False}

        mock_mr = Mock()
        mock_mr.changes.return_value = {"changes": [mock_change]}

        mock_project = Mock()
        mock_project.mergerequests.get.return_value = mock_mr
        mock_gl.projects.get.return_value = mock_project

        client = GitLabClient("https://gitlab.example.com", "token")
        changes = client.get_mr_changes("group/proj", 1)

        assert isinstance(changes, list)
        assert isinstance(changes[0], Change)
        assert changes[0].old_path == "a.py"


def test_get_mr_commits_maps_fields():
    with patch("src.gitlab_.client.gitlab.Gitlab") as mock_gitlab:
        mock_gl = Mock()
        mock_gitlab.return_value = mock_gl

        mock_commit = Mock()
        mock_commit.id = "abc"
        mock_commit.short_id = "abc"
        mock_commit.title = "T"
        mock_commit.message = "M"
        mock_commit.author_name = "A"
        mock_commit.author_email = "a@x"
        mock_commit.created_at = "now"

        mock_mr = Mock()
        mock_mr.commits.return_value = [mock_commit]

        mock_project = Mock()
        mock_project.mergerequests.get.return_value = mock_mr
        mock_gl.projects.get.return_value = mock_project

        client = GitLabClient("https://gitlab.example.com", "token")
        commits = client.get_mr_commits("group/proj", 1)

        assert isinstance(commits, list)
        assert isinstance(commits[0], Commit)
        assert commits[0].id == "abc"
