"""
Video Downloader - Support Douyin, Bilibili, Xiaohongshu
"""
import os
import re
import json
import asyncio
import time

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


async def _get_video_info_from_path(output_path: Path, platform: str, video_md5: str) -> Dict[str, Any]:
    """从下载的文件获取视频信息"""
    # 尝试从同名的json文件获取信息
    json_path = output_path.with_suffix('').with_suffix('.info.json')

    title = ""
    cover_url = ""
    duration = 0

    if json_path.exists():
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                video_info = json.load(f)
                title = video_info.get("title", "")
                cover_url = video_info.get("thumbnail", "")
                duration = video_info.get("duration", 0)
        except Exception as e:
            logger.warning(f"Failed to read info json: {e}")

    # 如果没有json信息，使用yt-dlp获取
    if not title:
        try:
            info_cmd = ["yt-dlp", "--dump-json", str(output_path)]
            process = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    info_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False
                )
            )
            if process.returncode == 0:
                video_info = json.loads(process.stdout)
                title = video_info.get("title", "")
                cover_url = video_info.get("thumbnail", "")
                duration = video_info.get("duration", 0)
        except Exception as e:
            logger.warning(f"Failed to get video info: {e}")
            title = output_path.stem

    return {
        "platform": platform,
        "video_id": video_md5,
        "title": title,
        "video_path": str(output_path),
        "cover_url": cover_url,
        "duration": duration
    }


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

        # 使用yt-dlp 下载视频
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
        video_md5 = self._generate_video_id(url)
        video_id = re.search(r'(\d+)', url).group(1)
        output_path = self.download_dir / f"{platform}_{video_md5}.mp4"

        # 检查视频是否已经下载过
        if output_path.exists() and output_path.stat().st_size > 0:
            logger.info(f"Video already exists: {output_path}")
            return await _get_video_info_from_path(output_path, platform, video_md5)

        # 构建yt-dlp命令
        cmd = [
            "yt-dlp",
            "--extractor-args", "douyin:imp=chrome;client_type=web",
            "--cookies", "cookies/cookies_douyin.txt",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "-o", str(output_path),
            "--no-playlist",
            f"https://www.douyin.com/note/{video_id}",
        ]

        try:
            # 使用run_in_executor在Windows上执行子进程
            loop = asyncio.get_event_loop()
            # 执行下载
            process = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=300,  # 5分钟超时
                    check=False,
                )
            )

            stderr_output = process.stderr.decode('utf-8', errors='ignore')

            # 处理 yt-dlp 的返回码
            if process.returncode != 0:
                # yt-dlp 返回非0不一定就是错误，可能是警告
                # 检查文件是否存在
                if output_path.exists() and output_path.stat().st_size > 0:
                    logger.warning(f"yt-dlp returned non-zero code but file exists. stderr: {stderr_output[:200]}")
                else:
                    logger.error(f"yt-dlp failed: {stderr_output}")
                    raise Exception(f"yt-dlp failed: {stderr_output}")

            # 等待文件生成
            file_ready = False
            for i in range(30):  # 最多等待30秒
                if output_path.exists() and output_path.stat().st_size > 0:
                    file_ready = True
                    break
                await asyncio.sleep(1)

            if not file_ready:
                raise Exception(f"File not ready after download: {output_path}")

            # 额外等待一小段时间确保文件写入完成
            await asyncio.sleep(0.5)

            file_size = output_path.stat().st_size
            logger.info(f"Video downloaded successfully: {output_path} ({file_size} bytes)")

            # 获取视频信息
            return await _get_video_info_from_path(output_path, platform, video_md5)

        except subprocess.TimeoutExpired:
            raise Exception("yt-dlp download timeout")
        except FileNotFoundError:
            raise Exception("yt-dlp not installed. Please install: pip install yt-dlp")
        except Exception as e:
            logger.error(f"Download error: {e}")
            raise

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
