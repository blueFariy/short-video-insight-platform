"""
Video Downloader - Support Douyin, Bilibili, Xiaohongshu
"""
import os
import re
import json
import asyncio
import aiohttp
import subprocess
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from loguru import logger

from app.core.config import settings


class VideoPlatform:
    """视频平台枚举"""
    DOUYIN = "douyin"
    BILIBILI = "bilibili"
    XIAOHONGSHU = "xiaohongshu"
    UNKNOWN = "unknown"


class VideoDownloader:
    """视频下载器"""

    def __init__(self):
        self.download_dir = Path(settings.VIDEO_DOWNLOAD_DIR)
        self.temp_dir = Path(settings.VIDEO_TEMP_DIR)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def download(self, url: str, platform: Optional[str] = None) -> Dict[str, Any]:
        """
        下载视频

        Args:
            url: 视频URL
            platform: 平台 (douyin/bilibili/xiaohongshu), 如果不指定则自动识别

        Returns:
            包含视频信息的字典
        """
        # 自动识别平台
        if not platform:
            platform = self._detect_platform(url)

        logger.info(f"Downloading video from {platform}: {url}")

        if platform == VideoPlatform.DOUYIN:
            return await self._download_douyin(url)
        elif platform == VideoPlatform.BILIBILI:
            return await self._download_bilibili(url)
        elif platform == VideoPlatform.XIAOHONGSHU:
            return await self._download_xiaohongshu(url)
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    def _detect_platform(self, url: str) -> str:
        """自动识别视频平台"""
        if "douyin.com" in url:
            return VideoPlatform.DOUYIN
        elif "bilibili.com" in url:
            return VideoPlatform.BILIBILI
        elif "xiaohongshu.com" in url or "xhslink.com" in url:
            return VideoPlatform.XIAOHONGSHU
        else:
            return VideoPlatform.UNKNOWN

    async def _download_douyin(self, url: str) -> Dict[str, Any]:
        """下载抖音视频"""
        # 提取视频ID
        video_id = self._extract_douyin_id(url)
        if not video_id:
            raise ValueError(f"Cannot extract video ID from URL: {url}")

        # 方法1: 使用移动端API (不需要cookies)
        try:
            mobile_api_url = f"https://aweme-hl.muscdn.com/aweme/v1/web/aweme/videostream/?aweme_id={video_id}&vr_type=0&is_play_url=1"

            async with aiohttp.ClientSession() as session:
                async with session.get(mobile_api_url, headers=self._get_headers()) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        video_url = data.get("play_url", {}).get("url") or data.get("data", {}).get("play_url", {}).get("url")

                        if video_url:
                            # 获取视频信息
                            info_url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={video_id}"
                            async with session.get(info_url, headers=self._get_headers()) as info_resp:
                                info_data = await info_resp.json() if info_resp.status == 200 else {}
                            video_info = info_data.get("aweme_detail", {})

                            title = video_info.get("desc", "")
                            cover_url = video_info.get("video", {}).get("cover", {}).get("url_list", [{}])[0].get("url")
                            duration = video_info.get("video", {}).get("duration", 0) / 1000

                            output_path = self.download_dir / f"douyin_{video_id}.mp4"
                            await self._download_file(video_url, output_path)

                            return {
                                "platform": VideoPlatform.DOUYIN,
                                "video_id": video_id,
                                "title": title,
                                "video_path": str(output_path),
                                "cover_url": cover_url,
                                "duration": duration
                            }
        except Exception as e:
            logger.warning(f"Mobile API method failed: {e}")

        # 方法2: 使用yt-dlp with extractor-args to bypass login
        try:
            return await self._download_with_ytdlp(url, VideoPlatform.DOUYIN)
        except Exception as e:
            logger.error(f"Douyin download failed: {e}")
            raise Exception(
                "抖音视频下载失败。需要提供Cookie或使用其他方式。\n"
                "解决方法：\n"
                "1. 在浏览器中登录抖音\n"
                "2. 获取浏览器Cookie\n"
                "3. 使用 --extractor-args 'douyin:imp=1' 参数\n"
                f"原始错误: {str(e)}"
            )

    def _extract_douyin_id(self, url: str) -> str:
        """提取抖音视频ID"""
        # 处理各种URL格式
        patterns = [
            r'/video/(\d+)',
            r'/v/(\d+)',
            r'https://v\.douyin\.com/(\w+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return ""

    async def _download_bilibili(self, url: str) -> Dict[str, Any]:
        """下载B站视频"""
        try:
            # 提取B站视频ID
            bvid = self._extract_bilibili_id(url)

            # 获取视频信息API
            api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"

            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as resp:
                    data = await resp.json()
                    video_data = data.get("data", {})

                    title = video_data.get("title", "")
                    duration = video_data.get("duration", 0)
                    cover_url = video_data.get("pic", "")

                    # 获取下载URL (需要登录或有权限)
                    # 这里使用yt-dlp作为回退方案
                    raise Exception("Use yt-dlp for download")

        except Exception as e:
            logger.error(f"Bilibili download failed: {e}")
            return await self._download_with_ytdlp(url, VideoPlatform.BILIBILI)

    def _extract_bilibili_id(self, url: str) -> str:
        """提取B站视频BV号"""
        patterns = [
            r'BV(\w+)',
            r'bvid=(\w+)',
            r'/video/(BV\w+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return ""

    async def _download_xiaohongshu(self, url: str) -> Dict[str, Any]:
        """下载小红书视频"""
        try:
            # 小红书视频下载较为复杂，需要解析页面
            # 使用浏览器自动化或第三方API
            # 这里使用yt-dlp作为主要方案
            return await self._download_with_ytdlp(url, VideoPlatform.XIAOHONGSHU)
        except Exception as e:
            logger.error(f"Xiaohongshu download failed: {e}")
            raise

    async def _download_with_ytdlp(self, url: str, platform: str) -> Dict[str, Any]:
        """使用yt-dlp下载视频"""
        video_id = self._generate_video_id(url)
        output_path = self.download_dir / f"{platform}_{video_id}.mp4"

        cmd = [
            "yt-dlp",
            "--extractor-args", "douyin:imp=chrome;client_type=web",
            "--cookies", "cookies_douyin.txt",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "-o", str(output_path),
            "--no-playlist",
            url
        ]

        try:
            # 使用run_in_executor在Windows上执行子进程
            loop = asyncio.get_event_loop()
            process = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False
                )
            )

            if process.returncode == 0:
                # 获取视频信息
                info_cmd = ["yt-dlp", "--dump-json", url]
                info_process = await loop.run_in_executor(
                    None,
                    lambda: subprocess.run(
                        info_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=False
                    )
                )
                video_info = json.loads(info_process.stdout)

                return {
                    "platform": platform,
                    "video_id": video_id,
                    "title": video_info.get("title", ""),
                    "video_path": str(output_path),
                    "cover_url": video_info.get("thumbnail", ""),
                    "duration": video_info.get("duration", 0)
                }
            else:
                raise Exception(f"yt-dlp failed: {process.stderr.decode()}")
        except FileNotFoundError:
            raise Exception("yt-dlp not installed. Please install: pip install yt-dlp")

    async def _download_file(self, url: str, output_path: Path) -> None:
        """下载文件"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self._get_headers()) as resp:
                if resp.status == 200:
                    with open(output_path, "wb") as f:
                        async for chunk in resp.content.iter_chunked(8192):
                            f.write(chunk)
                else:
                    raise Exception(f"Download failed with status {resp.status}")

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    def _generate_video_id(self, url: str) -> str:
        """生成视频ID"""
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()[:12]


video_downloader = VideoDownloader()
