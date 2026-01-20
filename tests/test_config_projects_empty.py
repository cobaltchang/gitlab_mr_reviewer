"""
測試當 GITLAB_PROJECTS 為空時，Config.from_env 會拋出 ConfigError
"""

import pytest
from src.utils.exceptions import ConfigError
from src.config import Config


def test_projects_env_empty(monkeypatch):
    monkeypatch.setenv("GITLAB_URL", "https://gitlab.example.com")
    monkeypatch.setenv("GITLAB_TOKEN", "token")
    monkeypatch.setenv("GITLAB_PROJECTS", " , , ")

    with pytest.raises(ConfigError):
        Config.from_env()
