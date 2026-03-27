"""
Subtitle Extraction Service
从视频中提取字幕文件
"""
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

from app.core.config import settings


class SubtitleService:
    """字幕提取服务"""

    def __init__(self):
        self.subtitle_dir = Path(settings.VIDEO_TEMP_DIR) / "subtitles"
        self.subtitle_dir.mkdir(parents=True, exist_ok=True)

    async def extract_subtitle(self, video_path: str) -> Dict[str, Any]:
        """
        提取视频字幕

        Args:
            video_path: 视频文件路径

        Returns:
            字幕信息字典
        """
        video_path = Path(video_path)
        base_name = video_path.stem

        # 查找同目录下的字幕文件
        subtitle_paths = [
            video_path.parent / f"{base_name}.srt",
            video_path.parent / f"{base_name}.vtt",
            video_path.parent / f"{base_name}.ass",
            video_path.parent / f"{base_name}.ssa",
            video_path.parent / f"{base_name}.txt",
        ]

        subtitle_text = ""
        subtitle_path = ""

        for path in subtitle_paths:
            if path.exists():
                subtitle_path = str(path)
                subtitle_text = self._read_subtitle_file(path)
                if subtitle_text.strip():
                    logger.info(f"Found subtitle file: {path}")
                    break

        # 如果没找到字幕文件，尝试在subtitle_dir中查找
        if not subtitle_text:
            for ext in ['.srt', '.vtt', '.ass', '.ssa', '.txt']:
                matching_files = list(self.subtitle_dir.glob(f"*{ext}"))
                for file in matching_files:
                    if base_name in file.name or file.stem.replace('_', '').replace('-', '') in base_name.replace('_', '').replace('-', ''):
                        subtitle_text = self._read_subtitle_file(file)
                        if subtitle_text.strip():
                            subtitle_path = str(file)
                            break
                if subtitle_text:
                    break

        if not subtitle_text:
            logger.info(f"No subtitle found for: {video_path.name}")
            return {
                "has_subtitle": False,
                "text": "",
                "path": "",
                "source": "none"
            }

        return {
            "has_subtitle": True,
            "text": subtitle_text,
            "path": subtitle_path,
            "source": self._detect_source(subtitle_path)
        }

    def _read_subtitle_file(self, path: Path) -> str:
        """读取字幕文件内容"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 如果是SRT/VTT格式，提取纯文本
            if path.suffix.lower() in ['.srt', '.vtt']:
                return self._extract_text_from_srt_vtt(content)
            # ASS/SSA格式
            elif path.suffix.lower() in ['.ass', '.ssa']:
                return self._extract_text_from_ass(content)
            # 纯文本格式
            else:
                return content.strip()

        except UnicodeDecodeError:
            try:
                with open(path, 'r', encoding='gbk') as f:
                    content = f.read()
                    return self._extract_text_from_srt_vtt(content) if path.suffix.lower() in ['.srt', '.vtt'] else content.strip()
            except Exception as e:
                logger.warning(f"Failed to read subtitle file {path}: {e}")
                return ""
        except Exception as e:
            logger.warning(f"Failed to read subtitle file {path}: {e}")
            return ""

    def _extract_text_from_srt_vtt(self, content: str) -> str:
        """从SRT/VTT格式提取纯文本"""
        lines = content.split('\n')
        text_lines = []

        for line in lines:
            line = line.strip()
            # 跳过序号、时间轴、空行、标签
            if not line:
                continue
            if re.match(r'^\d+$', line):
                continue
            if re.match(r'^\d{2}:\d{2}:\d{2}', line):
                continue
            if re.match(r'^WEBVTT', line):
                continue
            if line.startswith('<'):
                # 移除HTML标签
                line = re.sub(r'<[^>]+>', '', line)
            if line:
                text_lines.append(line)

        return ' '.join(text_lines)

    def _extract_text_from_ass(self, content: str) -> str:
        """从ASS/SSA格式提取纯文本"""
        lines = content.split('\n')
        text_lines = []
        in_events = False

        for line in lines:
            line = line.strip()
            if line.startswith('[Events]'):
                in_events = True
                continue
            if line.startswith('[') and in_events:
                break
            if in_events and line.startswith('Dialogue:'):
                # 提取Dialogue后的文本
                parts = line.split(',', 9)
                if len(parts) > 9:
                    text = parts[9]
                    # 移除样式标签
                    text = re.sub(r'\{[^}]+\}', '', text)
                    text = text.replace('\\N', ' ').replace('\\n', ' ')
                    if text.strip():
                        text_lines.append(text.strip())

        return ' '.join(text_lines)

    def _detect_source(self, path: str) -> str:
        """检测字幕来源"""
        path_lower = path.lower()
        if 'youtube' in path_lower or 'ytdl' in path_lower:
            return "youtube"
        elif 'bilibili' in path_lower or 'bili' in path_lower:
            return "bilibili"
        elif 'douyin' in path_lower:
            return "douyin"
        elif 'xiaohongshu' in path_lower or 'xhs' in path_lower:
            return "xiaohongshu"
        else:
            return "downloaded"


subtitle_service = SubtitleService()
