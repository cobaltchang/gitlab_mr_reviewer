"""
GitLab 客戶端測試
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from src.gitlab_.client import GitLabClient
from src.utils.exceptions import GitLabError


class TestGitLabClient:
    """GitLab 客戶端的測試"""

    def test_gitlab_client_init_success(self):
        """成功初始化 GitLab 客戶端"""
        with patch("src.gitlab_.client.gitlab.Gitlab") as mock_gitlab:
            mock_gl_instance = Mock()
            mock_gitlab.return_value = mock_gl_instance
            mock_gl_instance.auth.return_value = None
            
            client = GitLabClient("https://gitlab.example.com", "test_token")
            
            assert client is not None
            mock_gitlab.assert_called_once()

    def test_gitlab_client_init_failure(self):
        """初始化失敗時應該拋出 GitLabError"""
        with patch("src.gitlab_.client.gitlab.Gitlab") as mock_gitlab:
            mock_gitlab.side_effect = Exception("連接失敗")
            
            with pytest.raises(GitLabError):
                GitLabClient("https://gitlab.example.com", "invalid_token")

    def test_get_project_success(self):
        """成功取得專案"""
        with patch("src.gitlab_.client.gitlab.Gitlab") as mock_gitlab:
            mock_gl = Mock()
            mock_gitlab.return_value = mock_gl
            
            mock_project = Mock()
            mock_project.id = 123
            mock_project.name = "test-project"
            mock_gl.projects.get.return_value = mock_project
            
            client = GitLabClient("https://gitlab.example.com", "test_token")
            project = client.get_project("group/project")
            
            assert project is not None

    def test_get_project_not_found(self):
        """專案不存在時應該拋出 GitLabError"""
        with patch("src.gitlab_.client.gitlab.Gitlab") as mock_gitlab:
            mock_gl = Mock()
            mock_gitlab.return_value = mock_gl
            mock_gl.projects.get.side_effect = Exception("專案不存在")
            
            client = GitLabClient("https://gitlab.example.com", "test_token")
            
            with pytest.raises(GitLabError):
                client.get_project("nonexistent/project")

    def test_get_merge_requests_empty(self):
        """取得空的 MR 列表"""
        with patch("src.gitlab_.client.gitlab.Gitlab") as mock_gitlab:
            mock_gl = Mock()
            mock_gitlab.return_value = mock_gl
            
            mock_project = Mock()
            mock_project.mergerequests.list.return_value = []
            mock_gl.projects.get.return_value = mock_project
            
            client = GitLabClient("https://gitlab.example.com", "test_token")
            mrs = client.get_merge_requests("group/project")
            
            assert mrs == []

    def test_get_merge_requests_with_data(self):
        """取得有資料的 MR 列表"""
        with patch("src.gitlab_.client.gitlab.Gitlab") as mock_gitlab:
            mock_gl = Mock()
            mock_gitlab.return_value = mock_gl
            
            mock_mr = Mock()
            mock_mr.id = 1
            mock_mr.iid = 100
            mock_mr.title = "Test MR"
            
            mock_project = Mock()
            mock_project.mergerequests.list.return_value = [mock_mr]
            mock_gl.projects.get.return_value = mock_project
            
            client = GitLabClient("https://gitlab.example.com", "test_token")
            mrs = client.get_merge_requests("group/project")
            
            assert len(mrs) == 1
