from src.gitlab_.client import GitLabClient
from src.gitlab_.models import MRInfo


class DummyMR:
    def __init__(self):
        self.id = 11
        self.iid = 22
        self.title = "T"
        self.description = "D"
        self.state = "opened"
        self.author = {"username": "alice"}
        self.created_at = "2020-01-01"
        self.updated_at = "2020-01-02"
        self.source_branch = "feature/x"
        self.target_branch = "main"
        self.web_url = "http://"
        self.draft = None
        self.work_in_progress = False


class DummyProject:
    def __init__(self):
        self.id = 99
        self.path_with_namespace = "group/proj"

        class MRList:
            def get(self, iid):
                return DummyMR()

        self.mergerequests = MRList()


def test_get_mr_details_returns_mrinfo(monkeypatch):
    client = GitLabClient.__new__(GitLabClient)

    dummy_project = DummyProject()

    # Patch get_project to return our dummy project
    monkeypatch.setattr(client, "get_project", lambda project_id: dummy_project)

    mrinfo = client.get_mr_details("group/proj", 22)

    assert isinstance(mrinfo, MRInfo)
    assert mrinfo.iid == 22
    assert mrinfo.author == "alice"
