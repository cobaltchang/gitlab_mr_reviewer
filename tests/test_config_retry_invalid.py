"""
測試 Config.from_env 對非法 API_RETRY_COUNT 的行為
"""

import os
import pytest

from src.config import Config
from src.utils.exceptions import ConfigError


def test_invalid_api_retry_count(monkeypatch):
    monkeypatch.setenv("GITLAB_URL", "https://gitlab.example.com")
    monkeypatch.setenv("GITLAB_TOKEN", "token")
    monkeypatch.setenv("GITLAB_PROJECTS", "group/proj")
    monkeypatch.setenv("API_RETRY_COUNT", "not-an-int")

    with pytest.raises(ValueError):
        Config.from_env()
