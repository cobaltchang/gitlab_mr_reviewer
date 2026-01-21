"""
應用設定管理模組
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from src.utils.exceptions import ConfigError


@dataclass
class Config:
    """應用設定"""
    
    # 必要設定（無預設值）
    gitlab_url: str
    gitlab_token: str
    projects: List[str]
    
    # 可選設定（有預設值）
    reviews_path: str = "~/GIT_POOL/reviews"
    state_dir: str = "./state"
    db_path: str = "./state/mr_state.sqlite"
    gitlab_ssl_verify: bool = True
    log_level: str = "INFO"
    api_retry_count: int = 3
    
    @classmethod
    def from_env(cls) -> "Config":
        """
        從環境變數載入設定
        
        必要環境變數:
        - GITLAB_URL: GitLab 執行個體 URL
        - GITLAB_TOKEN: GitLab 存取令牌
        - GITLAB_PROJECTS_FILE 或 GITLAB_PROJECTS: 專案清單
          - GITLAB_PROJECTS_FILE: 檔案路徑（每行一個專案，推薦方式）
          - GITLAB_PROJECTS: 逗號分隔的專案清單（向後相容）
        
        可選環境變數:
        - REVIEWS_PATH: Worktree 根目錄 (預設: ~/GIT_POOL/reviews)
        - STATE_DIR: 狀態儲存目錄 (預設: ./state)
        - DB_PATH: SQLite 資料庫路徑
        - GITLAB_SSL_VERIFY: SSL 驗證 (預設: true)
        - LOG_LEVEL: 日誌級別 (預設: INFO)
        - API_RETRY_COUNT: API 重試次數 (預設: 3)
        """
        # 取得必要環境變數
        gitlab_url = os.getenv("GITLAB_URL")
        gitlab_token = os.getenv("GITLAB_TOKEN")
        projects_file = os.getenv("GITLAB_PROJECTS_FILE")
        projects_str = os.getenv("GITLAB_PROJECTS")
        
        # 驗證必要變數
        if not gitlab_url:
            raise ConfigError("缺少 GITLAB_URL 環境變數")
        if not gitlab_token:
            raise ConfigError("缺少 GITLAB_TOKEN 環境變數")
        
        # 從檔案或環境變數讀取專案清單
        if projects_file:
            # 優先使用檔案方式
            projects = cls._load_projects_from_file(projects_file)
        elif projects_str:
            # 向後相容：支援逗號分隔的專案清單
            projects = [p.strip() for p in projects_str.split(",") if p.strip()]
            if not projects:
                raise ConfigError("GITLAB_PROJECTS 為空")
        else:
            raise ConfigError("必須指定 GITLAB_PROJECTS_FILE 或 GITLAB_PROJECTS 環境變數")
        
        # 取得可選環境變數
        reviews_path = os.getenv("REVIEWS_PATH", "~/GIT_POOL/reviews")
        state_dir = os.getenv("STATE_DIR", "./state")
        db_path = os.getenv("DB_PATH", "./state/mr_state.sqlite")
        
        # 解析布林值
        ssl_verify_str = os.getenv("GITLAB_SSL_VERIFY", "true").lower()
        gitlab_ssl_verify = ssl_verify_str in ("true", "1", "yes")
        
        log_level = os.getenv("LOG_LEVEL", "INFO")
        api_retry_count = int(os.getenv("API_RETRY_COUNT", "3"))
        
        # 建立設定物件
        config = cls(
            gitlab_url=gitlab_url,
            gitlab_token=gitlab_token,
            projects=projects,
            reviews_path=reviews_path,
            state_dir=state_dir,
            db_path=db_path,
            gitlab_ssl_verify=gitlab_ssl_verify,
            log_level=log_level,
            api_retry_count=api_retry_count,
        )
        
        # 建立所需目錄
        config._create_directories()
        
        return config
    
    @staticmethod
    def _load_projects_from_file(file_path: str) -> List[str]:
        """
        從檔案讀取專案清單
        
        檔案格式：每行一個專案路徑，忽略空行和以 # 開頭的註釋行
        
        Args:
            file_path: 專案清單檔案路徑
            
        Returns:
            專案清單
            
        Raises:
            ConfigError: 檔案不存在或讀取失敗
        """
        try:
            path = Path(file_path).expanduser()
            
            if not path.exists():
                raise ConfigError(f"專案清單檔案不存在: {file_path}")
            
            projects = []
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    # 移除行首尾空格
                    line = line.strip()
                    
                    # 忽略空行和註釋行
                    if line and not line.startswith('#'):
                        projects.append(line)
            
            if not projects:
                raise ConfigError(f"專案清單檔案為空: {file_path}")
            
            return projects
        except FileNotFoundError:
            raise ConfigError(f"專案清單檔案不存在: {file_path}")
        except IOError as e:
            raise ConfigError(f"讀取專案清單檔案失敗: {file_path} - {e}")
    
    def _create_directories(self):
        """建立所需的目錄"""
        # 展開 ~ 符號
        reviews_path = Path(self.reviews_path).expanduser()
        state_dir = Path(self.state_dir).expanduser()
        
        # 建立目錄
        reviews_path.mkdir(parents=True, exist_ok=True)
        state_dir.mkdir(parents=True, exist_ok=True)
