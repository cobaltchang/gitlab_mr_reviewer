"""
日誌系統模組
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_dir: str = "logs") -> logging.Logger:
    """
    設定應用日誌系統
    
    Args:
        log_level: 日誌級別 (DEBUG, INFO, WARNING, ERROR)
        log_dir: 日誌目錄
        
    Returns:
        配置後的 Logger 物件
    """
    # 建立日誌目錄
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # 建立 logger
    logger = logging.getLogger("gitlab_mr_reviewer")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除現有的 handlers
    logger.handlers.clear()
    
    # 建立格式化程式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # 控制台輸出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 檔案輸出（使用 RotatingFileHandler）
    log_file = log_path / "app.log"
    file_handler = RotatingFileHandler(
        str(log_file),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


# 建立全域 logger 實例
logger = setup_logging()
