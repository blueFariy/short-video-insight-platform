"""
Log Configuration
"""
import sys
from pathlib import Path
from loguru import logger
from typing import Optional

from app.core.config import settings


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    配置日志系统

    Args:
        log_level: 日志级别
        log_file: 日志文件路径
    """
    # 移除默认处理器
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )

    # 文件输出
    log_path = log_file or "logs/app.log"
    log_dir = Path(log_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation="500 MB",
        retention="10 days",
        compression="zip",
        encoding="utf-8"
    )

    # 错误日志单独文件
    logger.add(
        "logs/error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="100 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )


# 初始化日志
def init_logging() -> None:
    """初始化日志系统"""
    setup_logging(
        log_level="DEBUG" if settings.DEBUG else "INFO",
        log_file="logs/user-service.log"
    )
