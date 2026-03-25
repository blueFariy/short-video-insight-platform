"""
Keyframe Extraction - Using FFmpeg
"""
import os
import json
import asyncio
import subprocess
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from loguru import logger

from app.core.config import settings


class KeyframeExtractor:
    """关键帧抽取器"""

    def __init__(self):
        self.temp_dir = Path(settings.VIDEO_TEMP_DIR)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def extract_keyframes(
        self,
        video_path: str,
        method: str = "scene_change",
        num_frames: int = 10
    ) -> Dict[str, Any]:
        """
        抽取关键帧

        Args:
            video_path: 视频文件路径
            method: 抽取方法 (scene_change/均匀采样/智能抽取)
            num_frames: 抽取帧数

        Returns:
            关键帧信息字典
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        logger.info(f"Extracting keyframes from {video_path.name}, method={method}")

        # 获取视频信息
        video_info = await self.get_video_info(video_path)
        duration = video_info.get("duration", 0)

        if method == "scene_change":
            keyframes = await self._extract_scene_changes(video_path, num_frames)
        elif method == "uniform":
            keyframes = await self._extract_uniform_frames(video_path, num_frames, duration)
        else:
            keyframes = await self._extract_smart_frames(video_path, num_frames, duration)

        return {
            "video_path": str(video_path),
            "video_duration": duration,
            "keyframes": keyframes,
            "total_frames": len(keyframes),
            "extracted_at": datetime.utcnow().isoformat()
        }

    async def get_video_info(self, video_path: Path) -> Dict[str, Any]:
        """获取视频信息"""
        cmd = [
            settings.FFPROBE_PATH,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path)
        ]

        try:
            loop = asyncio.get_event_loop()
            process = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            )

            if process.returncode == 0:
                data = json.loads(process.stdout)
                return self._parse_video_info(data)
            else:
                logger.warning("ffprobe failed, using file stats")
                return self._get_basic_info(video_path)
        except FileNotFoundError:
            logger.warning("ffprobe not found, using basic info")
            return self._get_basic_info(video_path)

    def _parse_video_info(self, data: Dict) -> Dict[str, Any]:
        """解析视频信息"""
        video_stream = None
        audio_stream = None

        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
            elif stream.get("codec_type") == "audio":
                audio_stream = stream

        duration = float(data.get("format", {}).get("duration", 0))

        return {
            "duration": duration,
            "width": video_stream.get("width", 0) if video_stream else 0,
            "height": video_stream.get("height", 0) if video_stream else 0,
            "codec": video_stream.get("codec_name", "") if video_stream else "",
            "fps": self._parse_fps(video_stream.get("r_frame_rate", "0/1")) if video_stream else 0,
            "bitrate": int(data.get("format", {}).get("bit_rate", 0)),
            "has_audio": audio_stream is not None,
            "audio_codec": audio_stream.get("codec_name", "") if audio_stream else ""
        }

    def _parse_fps(self, fps_str: str) -> float:
        """解析帧率"""
        try:
            num, den = fps_str.split("/")
            return float(num) / float(den) if float(den) != 0 else 0
        except:
            return 0

    def _get_basic_info(self, video_path: Path) -> Dict[str, Any]:
        """获取基础信息"""
        import mimetypes
        size = video_path.stat().st_size

        # 估算时长 (假设平均码率)
        estimated_duration = size / (1024 * 1024 * 2)  # 假设2Mbps

        return {
            "duration": estimated_duration,
            "size": size,
            "estimated": True
        }

    async def _extract_scene_changes(
        self,
        video_path: Path,
        num_frames: int
    ) -> List[Dict[str, Any]]:
        """基于场景变化抽取关键帧"""
        # 使用ffmpeg的select过滤器检测场景变化
        output_dir = self.temp_dir / f"{video_path.stem}_keyframes"
        output_dir.mkdir(exist_ok=True)

        # scene_change检测阈值 (默认0.4)
        cmd = [
            settings.FFMPEG_PATH,
            "-i", str(video_path),
            "-vf", f"select='gt(scene,0.4)',showinfo",
            "-fps_mode", "passthrough",
            "-frame_pts", "1",
            "-q:v", "2",
            f"{output_dir}/frame_%04d.jpg",
            "-v", "quiet"
        ]

        try:
            loop = asyncio.get_event_loop()
            process = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            )

            # 获取抽取的帧
            frames = []
            for img_file in sorted(output_dir.glob("frame_*.jpg"))[:num_frames]:
                frames.append({
                    "path": str(img_file),
                    "timestamp": self._get_frame_timestamp(img_file.name),
                    "type": "scene_change"
                })

            return frames

        except Exception as e:
            logger.error(f"Scene change extraction failed: {e}")
            # 回退到均匀采样
            return await self._extract_uniform_frames(video_path, num_frames, 60)

    async def _extract_uniform_frames(
        self,
        video_path: Path,
        num_frames: int,
        duration: float
    ) -> List[Dict[str, Any]]:
        """均匀采样抽取关键帧"""
        if duration <= 0:
            duration = 60

        output_dir = self.temp_dir / f"{video_path.stem}_keyframes"
        output_dir.mkdir(exist_ok=True)

        # 计算采样间隔
        interval = duration / num_frames

        frames = []
        for i in range(num_frames):
            timestamp = i * interval

            cmd = [
                settings.FFMPEG_PATH,
                "-ss", str(timestamp),
                "-i", str(video_path),
                "-vframes", "1",
                "-q:v", "2",
                f"{output_dir}/frame_{i:04d}.jpg",
                "-y",
                "-v", "quiet"
            ]

            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()

                frame_path = output_dir / f"frame_{i:04d}.jpg"
                if frame_path.exists():
                    frames.append({
                        "path": str(frame_path),
                        "timestamp": timestamp,
                        "type": "uniform"
                    })
            except Exception as e:
                logger.warning(f"Failed to extract frame at {timestamp}s: {e}")

        return frames

    async def _extract_smart_frames(
        self,
        video_path: Path,
        num_frames: int,
        duration: float
    ) -> List[Dict[str, Any]]:
        """智能关键帧抽取 (结合多种策略)"""
        # 策略：
        # 1. 开头帧 (0s)
        # 2. 中间帧
        # 3. 结尾帧
        # 4. 场景变化帧

        if duration <= 0:
            duration = 60

        frames = []

        # 开头、中间、结尾
        key_times = [0, duration / 2, duration - 1]

        output_dir = self.temp_dir / f"{video_path.stem}_keyframes"
        output_dir.mkdir(exist_ok=True)

        for i, timestamp in enumerate(key_times):
            cmd = [
                settings.FFMPEG_PATH,
                "-ss", str(timestamp),
                "-i", str(video_path),
                "-vframes", "1",
                "-q:v", "2",
                f"{output_dir}/keyframe_{i}.jpg",
                "-y",
                "-v", "quiet"
            ]

            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()

                frame_path = output_dir / f"keyframe_{i}.jpg"
                if frame_path.exists():
                    frames.append({
                        "path": str(frame_path),
                        "timestamp": timestamp,
                        "type": "smart_keyframe"
                    })
            except:
                pass

        # 补充场景变化帧
        remaining = num_frames - len(frames)
        if remaining > 0:
            scene_frames = await self._extract_scene_changes(video_path, remaining)
            frames.extend(scene_frames)

        return frames[:num_frames]

    def _get_frame_timestamp(self, filename: str) -> float:
        """从文件名获取时间戳"""
        # frame_0001.jpg -> 从showinfo解析
        # 这里简化处理，返回0
        return 0

    async def extract_frame_at_time(
        self,
        video_path: str,
        timestamp: float
    ) -> str:
        """在指定时间戳抽取单帧"""
        video_path = Path(video_path)
        output_path = self.temp_dir / f"{video_path.stem}_ts_{int(timestamp)}.jpg"

        cmd = [
            settings.FFMPEG_PATH,
            "-ss", str(timestamp),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path),
            "-y",
            "-v", "quiet"
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()

        if output_path.exists():
            return str(output_path)
        raise Exception(f"Failed to extract frame at {timestamp}s")


keyframe_extractor = KeyframeExtractor()
