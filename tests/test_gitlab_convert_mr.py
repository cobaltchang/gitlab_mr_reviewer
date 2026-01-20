"""
測試 GitLabClient._convert_mr_to_info 對 draft / work_in_progress 的相容性
"""

from src.gitlab_.client import GitLabClient
from src.gitlab_.models import MRInfo


class DummyMR:
    def __init__(self, id, iid, title, draft=None, work_in_progress=False):
        self.id = id
        self.iid = iid
        self.title = title
        self.description = ""
        self.state = "opened"
        self.author = {"username": "tester"}
        self.created_at = ""
        self.updated_at = ""
        self.source_branch = "f"
        self.target_branch = "m"
        self.web_url = ""
        if draft is not None:
            self.draft = draft
        self.work_in_progress = work_in_progress


class DummyProject:
    def __init__(self, id, path_with_namespace):
        self.id = id
        self.path_with_namespace = path_with_namespace


def test_convert_mr_prefers_draft_if_present():
    mr = DummyMR(id=1, iid=2, title="t", draft=True, work_in_progress=False)
    proj = DummyProject(id=10, path_with_namespace="group/proj")

    info = GitLabClient._convert_mr_to_info(mr, proj)
    assert isinstance(info, MRInfo)
    assert info.draft is True


def test_convert_mr_uses_work_in_progress_when_draft_missing():
    mr = DummyMR(id=2, iid=3, title="t2", draft=None, work_in_progress=True)
    proj = DummyProject(id=11, path_with_namespace="group/proj2")

    info = GitLabClient._convert_mr_to_info(mr, proj)
    assert isinstance(info, MRInfo)
    assert info.draft is True
    assert info.work_in_progress is True
