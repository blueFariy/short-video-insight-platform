"""
Video Processing Service - Main Service
Integrates: Download, Keyframe, ASR, OCR
"""
import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from loguru import logger

from app.services.downloader import video_downloader, VideoPlatform
from app.services.keyframe import keyframe_extractor
from app.services.asr import asr_service
from app.services.ocr import ocr_service


class VideoProcessor:
    """视频处理主服务"""

    def __init__(self):
        pass

    async def process_video(
        self,
        url: str,
        platform: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        完整处理视频

        Args:
            url: 视频URL
            platform: 视频平台
            options: 处理选项

        Returns:
            完整的视频分析结果
        """
        options = options or {}
        logger.info(f"Processing video: {url}")

        result = {
            "url": url,
            "platform": platform or video_downloader._detect_platform(url),
            "status": "processing",
            "started_at": datetime.utcnow().isoformat()
        }

        try:
            # 1. 下载视频
            logger.info("Step 1: Downloading video...")
            download_result = await video_downloader.download(url, platform)
            result["video_info"] = download_result
            result["video_path"] = download_result.get("video_path")
            result["title"] = download_result.get("title")
            result["cover_url"] = download_result.get("cover_url")
            result["duration"] = download_result.get("duration")

            # 2. 提取关键帧
            logger.info("Step 2: Extracting keyframes...")
            num_frames = options.get("num_keyframes", 10)
            keyframe_method = options.get("keyframe_method", "scene_change")
            keyframe_result = await keyframe_extractor.extract_keyframes(
                result["video_path"],
                method=keyframe_method,
                num_frames=num_frames
            )
            result["keyframes"] = keyframe_result.get("keyframes", [])
            result["keyframes_count"] = len(result["keyframes"])

            # 3. ASR语音识别
            logger.info("Step 3: Running ASR...")
            if options.get("skip_asr", False) is False:
                asr_result = await asr_service.recognize(
                    result["video_path"],
                    provider=options.get("asr_provider", "whisper"),
                    language=options.get("language", "zh")
                )
                result["asr"] = asr_result

            # 4. OCR文字识别
            logger.info("Step 4: Running OCR...")
            if options.get("skip_ocr", False) is False and result["keyframes"]:
                frame_paths = [kf["path"] for kf in result["keyframes"][:5]]  # 只识别前5帧
                ocr_result = await ocr_service.recognize_from_frames(
                    frame_paths,
                    provider=options.get("ocr_provider", "easyocr")
                )
                result["ocr"] = ocr_result

            # 处理完成
            result["status"] = "completed"
            result["completed_at"] = datetime.utcnow().isoformat()

            logger.info(f"Video processing completed: {result['title']}")
            return result

        except Exception as e:
            logger.error(f"Video processing failed: {e}")
            result["status"] = "failed"
            result["error"] = str(e)
            result["failed_at"] = datetime.utcnow().isoformat()
            raise

    async def download_only(
        self,
        url: str,
        platform: Optional[str] = None
    ) -> Dict[str, Any]:
        """仅下载视频"""
        return await video_downloader.download(url, platform)

    async def extract_keyframes_only(
        self,
        video_path: str,
        num_frames: int = 10,
        method: str = "scene_change"
    ) -> Dict[str, Any]:
        """仅提取关键帧"""
        return await keyframe_extractor.extract_keyframes(
            video_path,
            method=method,
            num_frames=num_frames
        )

    async def asr_only(
        self,
        video_path: str,
        provider: str = "whisper",
        language: str = "zh"
    ) -> Dict[str, Any]:
        """仅进行语音识别"""
        return await asr_service.recognize(video_path, provider, language)

    async def ocr_only(
        self,
        image_paths: List[str],
        provider: str = "easyocr"
    ) -> Dict[str, Any]:
        """仅进行文字识别"""
        return await ocr_service.recognize_from_frames(image_paths, provider)

    async def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """获取视频信息"""
        return await keyframe_extractor.get_video_info(Path(video_path))


video_processor = VideoProcessor()
