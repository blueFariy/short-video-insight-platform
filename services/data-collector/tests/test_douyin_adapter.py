"""
Tests for Douyin Adapter (基于 DouK-Downloader API)
"""
import asyncio

from app.adapters.douyin_adapter import DouyinAdapter,get_douyin_adapter

async def xx():
    adapter = get_douyin_adapter(cookie='cookies_douyin.txt')
    results = await adapter.get_trending_videos()
    for result in results:
        if result.title == '把春天妆在脸上':
            videos = await adapter.search_videos(result.title)
            print(videos)


# asyncio.run(xx())