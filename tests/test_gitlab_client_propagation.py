"""
測試當 GitLabClient.get_project 拋出 GitLabError 時，其他方法會重拋該錯誤
"""

from unittest.mock import patch
import pytest

from src.gitlab_.client import GitLabClient
from src.utils.exceptions import GitLabError


def _make_client_with_get_project_raising():
    client = GitLabClient.__new__(GitLabClient)
    # 手動建立 minimal attributes
    client.gl = None
    return client


def test_methods_propagate_gitlaberror(monkeypatch):
    # 建立實例並 patch get_project
    client = _make_client_with_get_project_raising()

    def raise_gitlab_error(project_id):
        raise GitLabError('project missing')

    monkeypatch.setattr(client, 'get_project', raise_gitlab_error)

    # 綁定 methods to the instance functions
    with pytest.raises(GitLabError):
        # call get_merge_requests which should call get_project and propagate
        from src.gitlab_.client import GitLabClient as C
        C.get_merge_requests(client, 'group/proj')

    with pytest.raises(GitLabError):
        from src.gitlab_.client import GitLabClient as C
        C.get_mr_details(client, 'group/proj', 1)

    with pytest.raises(GitLabError):
        from src.gitlab_.client import GitLabClient as C
        C.get_mr_changes(client, 'group/proj', 1)

    with pytest.raises(GitLabError):
        from src.gitlab_.client import GitLabClient as C
        C.get_mr_commits(client, 'group/proj', 1)
