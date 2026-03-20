"""
Video Downloader - Support Douyin, Bilibili, Xiaohongshu
"""
import os
import re
import json
import asyncio
import time
import hashlib

import aiohttp
import subprocess
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, parse_qs, urljoin
from pathlib import Path
from loguru import logger

from app.core.config import settings


class VideoPlatform:
    """视频平台枚举"""
    DOUYIN = "douyin"
    BILIBILI = "bilibili"
    XIAOHONGSHU = "xiaohongshu"
    UNKNOWN = "unknown"


class VideoDownloadError(Exception):
    """视频下载错误"""

    def __init__(self, message: str, platform: str = None, recoverable: bool = True):
        super().__init__(message)
        self.platform = platform
        self.recoverable = recoverable


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
            loop = asyncio.get_event_loop()
            process = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    ["yt-dlp", "--dump-json", str(output_path)],
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

        # Cookies 目录
        self.cookies_dir = "cookies"

        # User-Agent
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

        # 重试配置
        self.max_retries = 3
        self.retry_delay = 2

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

        # 重试机制
        last_error = None
        for attempt in range(self.max_retries):
            try:
                if platform == VideoPlatform.DOUYIN:
                    return await self._download_douyin(url)
                elif platform == VideoPlatform.BILIBILI:
                    return await self._download_bilibili(url)
                elif platform == VideoPlatform.XIAOHONGSHU:
                    return await self._download_xiaohongshu(url)
                else:
                    raise ValueError(f"Unsupported platform: {platform}")
            except VideoDownloadError as e:
                last_error = e
                if not e.recoverable or attempt == self.max_retries - 1:
                    raise
                logger.warning(f"Download attempt {attempt + 1} failed, retrying... Error: {e}")
                await asyncio.sleep(self.retry_delay * (attempt + 1))
            except Exception as e:
                last_error = e
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(f"Download attempt {attempt + 1} failed: {e}, retrying...")
                await asyncio.sleep(self.retry_delay * (attempt + 1))

        raise last_error

    def _detect_platform(self, url: str) -> str:
        """自动识别视频平台"""
        if "douyin.com" in url or "v.douyin.com" in url:
            return VideoPlatform.DOUYIN
        elif "bilibili.com" in url or "b23.tv" in url:
            return VideoPlatform.BILIBILI
        elif "xiaohongshu.com" in url or "xhslink.com" in url:
            return VideoPlatform.XIAOHONGSHU
        else:
            return VideoPlatform.UNKNOWN

    async def _download_douyin(self, url: str) -> Dict[str, Any]:
        """下载抖音视频"""
        # 先解析短链接
        resolved_url = await self._resolve_douyin_short_url(url)

        # 提取视频ID
        video_id = self._extract_douyin_id(resolved_url)
        if not video_id:
            raise VideoDownloadError(f"Cannot extract video ID from URL: {url}", VideoPlatform.DOUYIN,
                                     recoverable=False)

        # 使用yt-dlp下载视频
        return await self._download_with_ytdlp(
            f"https://www.douyin.com/note/{video_id}",  # note/可爬取，video/已经不能爬了 --2026.03.20
            VideoPlatform.DOUYIN,
            cookies_file=self._get_cookies_file(VideoPlatform.DOUYIN)
        )

    async def _resolve_douyin_short_url(self, url: str) -> str:
        """解析抖音短链接"""
        if "v.douyin.com" not in url:
            return url

        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, allow_redirects=True) as resp:
                    return str(resp.url)
        except Exception as e:
            logger.warning(f"Failed to resolve short URL: {e}")
            return url

    def _extract_douyin_id(self, url: str) -> str:
        """提取抖音视频ID"""
        # 处理各种URL格式
        patterns = [
            r'/video/(\d+)',  # https://www.douyin.com/video/7617451097011129646
            r'/note/(\d+)',  # https://www.douyin.com/note/7617451097011129646
            r'/v/(\d+)',  # https://www.douyin.com/v/xxx
            r'video_id=(\d+)',  # query string
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return ""

    def _get_cookies_file(self, platform: str) -> str:
        """获取平台的cookies文件"""
        cookies_map = {
            VideoPlatform.DOUYIN: "cookies_douyin.txt",
            VideoPlatform.BILIBILI: "cookies_bilibili.txt",
            VideoPlatform.XIAOHONGSHU: "cookies_xiaohongshu.txt",
        }

        filename = cookies_map.get(platform)
        if not filename:
            return None

        cookies_path = self.cookies_dir + '/' + filename
        return cookies_path

    async def _download_bilibili(self, url: str) -> Dict[str, Any]:
        """下载B站视频"""
        # 解析短链接
        resolved_url = await self._resolve_bilibili_short_url(url)

        # 提取BV号
        bvid = self._extract_bilibili_id(resolved_url)

        # 尝试使用API获取下载链接
        try:
            result = await self._download_bilibili_api(resolved_url, bvid)
            if result:
                return result
        except Exception as e:
            logger.warning(f"Bilibili API download failed: {e}")

        # 回退到yt-dlp
        return await self._download_with_ytdlp(
            resolved_url,
            VideoPlatform.BILIBILI,
            cookies_file=self._get_cookies_file(VideoPlatform.BILIBILI)
        )

    async def _resolve_bilibili_short_url(self, url: str) -> str:
        """解析B站短链接"""
        if "b23.tv" not in url:
            return url

        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, allow_redirects=True) as resp:
                    return str(resp.url)
        except Exception as e:
            logger.warning(f"Failed to resolve BiliBili short URL: {e}")
            return url

    async def _download_bilibili_api(self, url: str, bvid: str) -> Optional[Dict[str, Any]]:
        """使用B站API下载（需要登录）"""
        # 这里可以扩展为使用B站API下载
        # 目前回退到yt-dlp
        return None

    def _extract_bilibili_id(self, url: str) -> str:
        """提取B站视频BV号"""
        patterns = [
            r'/(BV\w+)',
            r'bvid=(\w+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return ""

    async def _download_xiaohongshu(self, url: str) -> Dict[str, Any]:
        """下载小红书视频"""
        return await self._download_with_ytdlp(
            url,
            VideoPlatform.XIAOHONGSHU,
            cookies_file=self._get_cookies_file(VideoPlatform.XIAOHONGSHU)
        )

    async def _download_with_ytdlp(
            self,
            url: str,
            platform: str,
            cookies_file: str,
    ) -> Dict[str, Any]:
        """使用yt-dlp下载视频"""
        video_md5 = self._generate_video_id(url)

        # 提取视频ID用于文件名
        video_id_match = re.search(r'(\d+)', url)
        video_id = video_id_match.group(1) if video_id_match else video_md5

        output_path = self.download_dir / f"{platform}_{video_md5}.mp4"
        info_json_path = output_path.with_suffix('').with_suffix('.info.json')

        # 检查视频是否已经下载过
        if output_path.exists() and output_path.stat().st_size > 0:
            logger.info(f"Video already exists: {output_path}")
            return await _get_video_info_from_path(output_path, platform, video_md5)

        # 构建yt-dlp命令
        cmd = [
            "yt-dlp",
            "--extractor-args", "douyin:imp=chrome;client_type=web",
            "--cookies", cookies_file,
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "-o", str(output_path),
            "--write-info-json",
            "--no-playlist",
            url,
        ]

        logger.info(f"Running yt-dlp command: {' '.join(cmd)}")

        try:
            loop = asyncio.get_event_loop()
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
                # 检查是否是cookies问题
                if "Fresh cookies" in stderr_output or "cookies" in stderr_output.lower():
                    raise VideoDownloadError(
                        f"Cookies过期或无效，请更新cookies文件: {stderr_output[:200]}",
                        platform,
                        recoverable=True
                    )

                # 检查文件是否存在（有时候返回非0但下载成功）
                if not (output_path.exists() and output_path.stat().st_size > 0):
                    logger.error(f"yt-dlp failed: {stderr_output}")
                    raise VideoDownloadError(f"yt-dlp下载失败: {stderr_output[:200]}", platform, recoverable=True)

            # 等待文件生成
            file_ready = await self._wait_for_file(output_path, timeout=30)

            if not file_ready:
                raise VideoDownloadError(f"文件未生成: {output_path}", platform, recoverable=True)

            # 额外等待确保文件写入完成
            await asyncio.sleep(0.5)

            file_size = output_path.stat().st_size
            logger.info(f"Video downloaded successfully: {output_path} ({file_size} bytes)")

            # 获取视频信息
            return await _get_video_info_from_path(output_path, platform, video_md5)

        except subprocess.TimeoutExpired:
            raise VideoDownloadError("yt-dlp下载超时", platform, recoverable=True)
        except FileNotFoundError:
            raise VideoDownloadError("yt-dlp未安装，请运行: pip install yt-dlp", platform, recoverable=False)
        except VideoDownloadError:
            raise
        except Exception as e:
            logger.error(f"Download error: {e}")
            raise VideoDownloadError(f"下载出错: {str(e)}", platform, recoverable=True)

    def _get_extractor_args(self, platform: str) -> Optional[str]:
        """获取平台特定的extractor-args"""
        args_map = {
            VideoPlatform.DOUYIN: "douyin:imp=chrome;client_type=web",
            VideoPlatform.BILIBILI: "bilibili:imp=chrome",
            VideoPlatform.XIAOHONGSHU: "xiaohongshu:imp=chrome",
        }
        return args_map.get(platform)

    async def _wait_for_file(self, path: Path, timeout: int = 30) -> bool:
        """等待文件生成"""
        for i in range(timeout):
            if path.exists() and path.stat().st_size > 0:
                return True
            await asyncio.sleep(1)
        return False

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
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    def _generate_video_id(self, url: str) -> str:
        """生成视频ID"""
        return hashlib.md5(url.encode()).hexdigest()[:12]


video_downloader = VideoDownloader()
