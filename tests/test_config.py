"""
應用設定配置測試
"""

import os
import pytest
from pathlib import Path

from src.config import Config
from src.utils.exceptions import ConfigError


class TestConfig:
    """設定模組測試"""

    def test_config_from_env_with_valid_env(self, monkeypatch):
        """從有效的環境變數載入設定"""
        monkeypatch.setenv("GITLAB_URL", "https://gitlab.example.com")
        monkeypatch.setenv("GITLAB_TOKEN", "test_token_123")
        monkeypatch.setenv("GITLAB_PROJECTS", "group/project1,group/project2")
        monkeypatch.setenv("REVIEWS_PATH", "/tmp/reviews")
        
        config = Config.from_env()
        
        assert config.gitlab_url == "https://gitlab.example.com"
        assert config.gitlab_token == "test_token_123"
        assert len(config.projects) == 2
        assert config.projects[0] == "group/project1"

    def test_config_missing_required_env(self, monkeypatch):
        """缺少必要環境變數時應該拋出異常"""
        monkeypatch.delenv("GITLAB_URL", raising=False)
        monkeypatch.delenv("GITLAB_TOKEN", raising=False)
        monkeypatch.delenv("GITLAB_PROJECTS", raising=False)
        
        with pytest.raises(ConfigError):
            Config.from_env()

    def test_config_default_values(self, monkeypatch):
        """使用預設值的設定"""
        monkeypatch.setenv("GITLAB_URL", "https://gitlab.example.com")
        monkeypatch.setenv("GITLAB_TOKEN", "test_token")
        monkeypatch.setenv("GITLAB_PROJECTS", "group/project")
        
        config = Config.from_env()
        
        assert config.gitlab_ssl_verify is True
        assert config.log_level == "INFO"
        assert config.api_retry_count == 3

    def test_config_projects_parsing(self, monkeypatch):
        """專案清單的正確解析"""
        monkeypatch.setenv("GITLAB_URL", "https://gitlab.example.com")
        monkeypatch.setenv("GITLAB_TOKEN", "test_token")
        monkeypatch.setenv("GITLAB_PROJECTS", "group1/proj1,group2/proj2,group3/proj3")
        
        config = Config.from_env()
        
        assert len(config.projects) == 3
        assert config.projects == ["group1/proj1", "group2/proj2", "group3/proj3"]

    def test_load_projects_from_file_valid(self, tmp_path):
        """從有效檔案讀取專案清單"""
        # 建立測試檔案
        projects_file = tmp_path / "gitlab_projects.txt"
        projects_file.write_text(
            "# 註釋行\n"
            "group/project1\n"
            "group/project2\n"
            "\n"  # 空行
            "# 另一個註釋\n"
            "group/project3\n"
        )
        
        projects = Config._load_projects_from_file(str(projects_file))
        
        assert len(projects) == 3
        assert projects == ["group/project1", "group/project2", "group/project3"]

    def test_load_projects_from_file_not_found(self):
        """檔案不存在時應該拋出異常"""
        with pytest.raises(ConfigError) as exc_info:
            Config._load_projects_from_file("/nonexistent/path/gitlab_projects.txt")
        
        assert "檔案不存在" in str(exc_info.value)

    def test_load_projects_from_file_empty(self, tmp_path):
        """空檔案應該拋出異常"""
        projects_file = tmp_path / "gitlab_projects.txt"
        projects_file.write_text("# 只有註釋\n\n")
        
        with pytest.raises(ConfigError) as exc_info:
            Config._load_projects_from_file(str(projects_file))
        
        assert "檔案為空" in str(exc_info.value)

    def test_load_projects_from_file_with_tilde(self, tmp_path, monkeypatch):
        """支援路徑中的 ~ 符號"""
        # 模擬 home 目錄
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        monkeypatch.setenv("HOME", str(home_dir))
        
        projects_file = home_dir / "gitlab_projects.txt"
        projects_file.write_text("group/project1\ngroup/project2\n")
        
        # 使用 ~ 符號的路徑
        projects = Config._load_projects_from_file("~/gitlab_projects.txt")
        
        assert len(projects) == 2
        assert projects == ["group/project1", "group/project2"]

    def test_config_from_env_with_projects_file(self, tmp_path, monkeypatch):
        """使用檔案型式的專案清單"""
        # 建立專案檔案
        projects_file = tmp_path / "gitlab_projects.txt"
        projects_file.write_text("group/project1\ngroup/project2\n")
        
        monkeypatch.setenv("GITLAB_URL", "https://gitlab.example.com")
        monkeypatch.setenv("GITLAB_TOKEN", "test_token")
        monkeypatch.setenv("GITLAB_PROJECTS_FILE", str(projects_file))
        
        config = Config.from_env()
        
        assert len(config.projects) == 2
        assert config.projects == ["group/project1", "group/project2"]

    def test_config_ssl_verify_flag(self, monkeypatch):
        """SSL 驗證旗標的設定"""
        monkeypatch.setenv("GITLAB_URL", "https://gitlab.example.com")
        monkeypatch.setenv("GITLAB_TOKEN", "test_token")
        monkeypatch.setenv("GITLAB_PROJECTS", "group/project")
        monkeypatch.setenv("GITLAB_SSL_VERIFY", "false")
        
        config = Config.from_env()
        
        assert config.gitlab_ssl_verify is False

    def test_config_path_creation(self, monkeypatch, tmp_path):
        """設定路徑會自動建立"""
        test_path = tmp_path / "test_reviews"
        
        monkeypatch.setenv("GITLAB_URL", "https://gitlab.example.com")
        monkeypatch.setenv("GITLAB_TOKEN", "test_token")
        monkeypatch.setenv("GITLAB_PROJECTS", "group/project")
        monkeypatch.setenv("REVIEWS_PATH", str(test_path))
        
        config = Config.from_env()
        
        # 路徑會在載入時建立
        assert config.reviews_path == str(test_path)
