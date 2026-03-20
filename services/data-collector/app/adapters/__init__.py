"""
Platform Adapters
"""
from app.adapters.base import PlatformAdapter
from app.adapters.douyin_adapter import DouyinAdapter, get_douyin_adapter
from app.adapters.bilibili_adapter import BilibiliAdapter, bilibili_adapter
from app.adapters.xiaohongshu_adapter import XiaohongshuAdapter, xiaohongshu_adapter


def get_platform_adapter(platform: str) -> PlatformAdapter:
    """
    Get platform adapter by name

    Args:
        platform: Platform name (douyin/bilibili/xiaohongshu/kuaishou)

    Returns:
        Platform adapter instance
    """
    adapters = {
        'douyin': get_douyin_adapter(),
        'bilibili': bilibili_adapter,
        'xiaohongshu': xiaohongshu_adapter,
    }

    adapter = adapters.get(platform.lower())
    if not adapter:
        raise ValueError(f"Unsupported platform: {platform}")

    return adapter


__all__ = [
    'PlatformAdapter',
    'DouyinAdapter',
    'bilibili_adapter',
    'BilibiliAdapter',
    'XiaohongshuAdapter',
    'xiaohongshu_adapter',
    'get_platform_adapter'
]
