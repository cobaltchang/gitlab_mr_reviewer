"""
測試 init_app 初始化行為（使用 mock 注入以避免外部副作用）
"""

from types import SimpleNamespace
from unittest.mock import Mock

import src.main as main


def test_init_app_sets_globals(monkeypatch):
    # 準備 fake config
    fake_config = SimpleNamespace(
        gitlab_url="https://gitlab.example.com",
        gitlab_token="token",
        gitlab_ssl_verify=True,
        log_level="INFO",
        state_dir="./state",
        db_path="./state/db.sqlite",
        projects=["group/proj"],
        reviews_path="~/reviews",
    )

    monkeypatch.setattr('src.main.Config.from_env', lambda: fake_config)
    monkeypatch.setattr('src.main.setup_logging', lambda log_level, log_dir: Mock())

    # Patch GitLabClient, StateManager, MRScanner, WorktreeManager to simple mocks
    monkeypatch.setattr('src.main.GitLabClient', lambda url, token, ssl_verify: Mock())
    monkeypatch.setattr('src.main.StateManager', lambda db_path: Mock())
    # MRScanner and WorktreeManager will be instantiated in init_app; allow defaults

    # Call init_app
    main.init_app()

    assert main.config is not None
    assert main.gitlab_client is not None
    assert main.state_manager is not None
    assert main.mr_scanner is not None
    assert main.worktree_manager is not None
