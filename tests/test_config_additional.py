import builtins
import pytest
import os
from pathlib import Path

from src.config import Config
from src.utils.exceptions import ConfigError


def test_missing_gitlab_token_raises(monkeypatch):
    monkeypatch.delenv("GITLAB_TOKEN", raising=False)
    monkeypatch.setenv("GITLAB_URL", "https://gitlab.example.com")
    monkeypatch.setenv("GITLAB_PROJECTS", "proj/a")

    with pytest.raises(ConfigError) as exc:
        Config.from_env()

    assert "GITLAB_TOKEN" in str(exc.value)


def test_missing_projects_env_raises(monkeypatch):
    monkeypatch.setenv("GITLAB_URL", "https://gitlab.example.com")
    monkeypatch.setenv("GITLAB_TOKEN", "token")
    monkeypatch.delenv("GITLAB_PROJECTS", raising=False)
    monkeypatch.delenv("GITLAB_PROJECTS_FILE", raising=False)

    with pytest.raises(ConfigError) as exc:
        Config.from_env()

    assert "GITLAB_PROJECTS_FILE" in str(exc.value) or "GITLAB_PROJECTS" in str(exc.value)


def test_load_projects_from_file_file_not_found(monkeypatch, tmp_path):
    file_path = tmp_path / "does_not_exist.txt"

    # Force Path.exists to return True so open is attempted, then make open raise FileNotFoundError
    monkeypatch.setattr(Path, "exists", lambda self: True)

    def fake_open(*args, **kwargs):
        raise FileNotFoundError("boom")

    monkeypatch.setattr(builtins, "open", fake_open)

    with pytest.raises(ConfigError) as exc:
        Config._load_projects_from_file(str(file_path))

    assert "專案清單檔案不存在" in str(exc.value) or "讀取專案清單檔案失敗" in str(exc.value)
