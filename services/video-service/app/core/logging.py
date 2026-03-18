"""
Log Configuration
"""
import sys
from pathlib import Path
from loguru import logger


def setup_logging(log_level: str = "INFO", log_file: str = "logs/video-service.log") -> None:
    """配置日志系统"""
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )

    # 文件输出
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level=log_level,
        rotation="500 MB",
        retention="10 days",
        encoding="utf-8"
    )


def init_logging() -> None:
    """初始化日志系统"""
    setup_logging(log_level="DEBUG" if settings.DEBUG else "INFO")


# Import settings at module level
from app.core.config import settings
