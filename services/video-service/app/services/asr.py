"""
ASR Service - Automatic Speech Recognition
Support: 阿里云, 腾讯云, OpenAI Whisper
"""
import os
import json
import asyncio
import aiohttp
import subprocess
from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger

from app.core.config import settings


class ASRProvider:
    """ASR提供商枚举"""
    ALIYUN = "aliyun"
    TENCENT = "tencent"
    WHISPER = "whisper"


class ASRService:
    """语音识别服务"""

    def __init__(self):
        self.temp_dir = Path(settings.VIDEO_TEMP_DIR)

    async def recognize(
        self,
        video_path: str,
        provider: str = "whisper",
        language: str = "zh"
    ) -> Dict[str, Any]:
        """
        语音识别

        Args:
            video_path: 视频文件路径
            provider: ASR提供商 (aliyun/tencent/whisper)
            language: 语言代码

        Returns:
            识别结果
        """
        logger.info(f"ASR processing: {video_path}, provider={provider}")

        # 提取音频
        audio_path = await self._extract_audio(video_path)

        try:
            if provider == ASRProvider.ALIYUN:
                return await self._recognize_aliyun(audio_path, language)
            elif provider == ASRProvider.TENCENT:
                return await self._recognize_tencent(audio_path, language)
            else:
                return await self._recognize_whisper(audio_path, language)
        finally:
            # 清理临时音频文件
            if audio_path.exists():
                audio_path.unlink()

    async def _extract_audio(self, video_path: str) -> Path:
        """从视频提取音频"""
        video_path = Path(video_path)
        audio_path = self.temp_dir / f"{video_path.stem}.wav"

        # 使用ffmpeg提取音频 (16kHz, mono, 16bit)
        cmd = [
            settings.FFMPEG_PATH,
            "-i", str(video_path),
            "-vn",  # 不处理视频
            "-acodec", "pcm_s16le",  # PCM格式
            "-ar", "16000",  # 16kHz采样率
            "-ac", "1",  # 单声道
            str(audio_path),
            "-y",
            "-v", "quiet"
        ]

        loop = asyncio.get_event_loop()
        process = await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        )

        if not audio_path.exists():
            raise Exception("Audio extraction failed")

        return audio_path

    async def _recognize_whisper(self, audio_path: Path, language: str) -> Dict[str, Any]:
        """使用OpenAI Whisper进行识别"""
        try:
            # 尝试使用openai-whisper
            import whisper

            model = whisper.load_model("base")
            result = model.transcribe(str(audio_path), language=language)

            return {
                "provider": ASRProvider.WHISPER,
                "text": result["text"],
                "segments": result.get("segments", []),
                "language": result.get("language", language),
                "confidence": self._calculate_confidence(result)
            }
        except ImportError:
            # 回退到命令行whisper
            return await self._recognize_whisper_cli(audio_path, language)

    async def _recognize_whisper_cli(self, audio_path: Path, language: str) -> Dict[str, Any]:
        """使用whisper CLI进行识别"""
        cmd = [
            "whisper",
            str(audio_path),
            "--language", language,
            "--model", "base",
            "--output_format", "json"
        ]

        try:
            loop = asyncio.get_event_loop()
            process = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=self.temp_dir
                )
            )

            # 读取输出JSON
            json_path = audio_path.with_suffix(".json")
            if json_path.exists():
                with open(json_path, "r", encoding="utf-8") as f:
                    result = json.load(f)

                return {
                    "provider": ASRProvider.WHISPER,
                    "text": " ".join([seg["text"] for seg in result.get("segments", [])]),
                    "segments": result.get("segments", []),
                    "language": language
                }

            raise Exception("Whisper output not found")

        except FileNotFoundError:
            raise Exception("Whisper not installed. Install: pip install openai-whisper")

    async def _recognize_aliyun(self, audio_path: Path, language: str) -> Dict[str, Any]:
        """使用阿里云ASR进行识别"""
        if not settings.ALIYUN_ACCESS_KEY_ID:
            logger.warning("Aliyun credentials not set, using whisper")
            return await self._recognize_whisper(audio_path, language)

        # 阿里云ASR需要上传音频文件
        # 这里简化处理，实际需要调用SDK
        logger.info("Using Aliyun ASR")

        # 参考实现
        # from aliyunsdkcore.client import AcsClient
        # from aliyunsdkcore.request import CommonRequest
        # client = AcsClient(settings.ALIYUN_ACCESS_KEY_ID, settings.ALIYUN_ACCESS_KEY_SECRET, 'cn-shanghai')
        # request = CommonRequest()
        # request.set_accept_format('json')
        # request.set_domain('nls-gateway.cn-shanghai.aliyuncs.com')
        # ...

        raise NotImplementedError("Aliyun ASR implementation requires SDK setup")

    async def _recognize_tencent(self, audio_path: Path, language: str) -> Dict[str, Any]:
        """使用腾讯云ASR进行识别"""
        if not settings.TENCENT_SECRET_ID:
            logger.warning("Tencent credentials not set, using whisper")
            return await self._recognize_whisper(audio_path, language)

        logger.info("Using Tencent ASR")

        # 参考实现
        # from tencentcloud.asr.v20190614 import AsrClient, models
        # client = AsrClient(cred, "ap-shanghai")
        # req = models.DescribeRecognitionUsageRequest()
        # ...

        raise NotImplementedError("Tencent ASR implementation requires SDK setup")

    def _calculate_confidence(self, result: Dict) -> float:
        """计算识别置信度"""
        segments = result.get("segments", [])
        if not segments:
            return 0.0

        # 基于平均日志概率计算
        total_logprob = sum(seg.get("avg_logprob", 0) for seg in segments)
        avg_logprob = total_logprob / len(segments)

        # 转换为0-1的置信度
        confidence = 1 / (1 + abs(avg_logprob))
        return min(1.0, max(0.0, confidence))


asr_service = ASRService()
