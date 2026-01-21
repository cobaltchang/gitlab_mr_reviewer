"""
測試 GitLabClient._convert_mr_to_info 在 author 為 None 時回傳 unknown
"""

from src.gitlab_.client import GitLabClient
from src.gitlab_.models import MRInfo


class DummyMR:
    def __init__(self):
        self.id = 1
        self.iid = 2
        self.title = "t"
        self.description = ""
        self.state = "opened"
        self.author = None
        self.created_at = ""
        self.updated_at = ""
        self.source_branch = "f"
        self.target_branch = "m"
        self.web_url = ""


class DummyProject:
    def __init__(self):
        self.id = 99
        self.path_with_namespace = "g/p"


def test_convert_handles_author_none():
    mr = DummyMR()
    proj = DummyProject()

    info = GitLabClient._convert_mr_to_info(mr, proj)
    assert info.author == "unknown"
