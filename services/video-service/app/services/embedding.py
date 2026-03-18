"""
Embedding Service - Multimodal Embeddings
Support: OpenAI Embeddings, Gemini Embedding, CLIP
"""
import asyncio
import base64
import aiohttp
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from loguru import logger

from app.core.config import settings


class EmbeddingProvider:
    """Embedding提供商枚举"""
    OPENAI = "openai"
    GEMINI = "gemini"
    CLIP = "clip"


class EmbeddingService:
    """向量化服务"""

    def __init__(self):
        self.default_provider = self._detect_default_provider()
        self.dimension = 1536  # 默认维度 (OpenAI text-embedding-3-small)

    def _detect_default_provider(self) -> str:
        """检测默认provider"""
        if settings.OPENAI_API_KEY:
            return EmbeddingProvider.OPENAI
        elif settings.GEMINI_API_KEY:
            return EmbeddingProvider.GEMINI
        else:
            return EmbeddingProvider.CLIP

    async def embed_texts(
        self,
        texts: List[str],
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        文本向量化

        Args:
            texts: 文本列表
            provider: 向量化提供商
            model: 模型名称

        Returns:
            向量列表
        """
        provider = provider or self.default_provider
        logger.info(f"Embedding {len(texts)} texts with {provider}")

        if provider == EmbeddingProvider.OPENAI:
            return await self._embed_openai(texts, model)
        elif provider == EmbeddingProvider.GEMINI:
            return await self._embed_gemini(texts, model)
        elif provider == EmbeddingProvider.CLIP:
            return await self._embed_clip_texts(texts)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def embed_images(
        self,
        image_paths: List[str],
        provider: str = "clip"
    ) -> List[List[float]]:
        """
        图像向量化

        Args:
            image_paths: 图片路径列表
            provider: 向量化提供商

        Returns:
            向量列表
        """
        logger.info(f"Embedding {len(image_paths)} images with {provider}")

        if provider == EmbeddingProvider.CLIP:
            return await self._embed_clip_images(image_paths)
        else:
            raise ValueError(f"Image embedding not supported for {provider}")

    async def embed_video_frame(
        self,
        frame_path: str,
        provider: str = "clip"
    ) -> List[float]:
        """向量化单个视频帧"""
        results = await self.embed_images([frame_path], provider)
        return results[0]

    async def embed_video(
        self,
        video_info: Dict[str, Any],
        provider: str = "clip"
    ) -> Dict[str, Any]:
        """
        向量化整个视频

        Args:
            video_info: 视频信息（包含关键帧等）
            provider: 向量化提供商

        Returns:
            视频向量
        """
        vectors = []

        # 向量化关键帧
        if "keyframes" in video_info:
            frame_paths = [kf["path"] for kf in video_info["keyframes"]]
            frame_vectors = await self.embed_images(frame_paths, provider)
            vectors.extend(frame_vectors)

        # 向量化ASR文本
        if "asr" in video_info and video_info["asr"].get("text"):
            text_vector = await self.embed_texts([video_info["asr"]["text"]], provider)
            vectors.extend(text_vector)

        # 向量化OCR文本
        if "ocr" in video_info and video_info["ocr"].get("combined_text"):
            ocr_vector = await self.embed_texts([video_info["ocr"]["combined_text"]], provider)
            vectors.extend(ocr_vector)

        # 计算平均向量
        if vectors:
            avg_vector = [sum(x) / len(vectors) for x in zip(*vectors)]
        else:
            avg_vector = []

        return {
            "video_id": video_info.get("video_id"),
            "vector": avg_vector,
            "frame_count": len(video_info.get("keyframes", [])),
            "vectors_count": len(vectors),
            "provider": provider
        }

    async def _embed_openai(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """使用OpenAI进行向量化"""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not configured")

        model = model or settings.OPENAI_EMBEDDING_MODEL

        # 设置维度
        dimensions = None
        if "text-embedding-3" in model:
            dimensions = 1536

        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }

            payload = {
                "input": texts,
                "model": model
            }
            if dimensions:
                payload["dimensions"] = dimensions

            async with session.post(
                "https://api.openai.com/v1/embeddings",
                headers=headers,
                json=payload
            ) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    raise Exception(f"OpenAI API error: {error}")

                result = await resp.json()
                return [item["embedding"] for item in result["data"]]

    async def _embed_gemini(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """使用Gemini进行向量化"""
        if not settings.GEMINI_API_KEY:
            raise ValueError("Gemini API key not configured")

        # Gemini embedding API
        # 注意: 需要确认API可用性
        model = model or "gemini-embedding-001"

        vectors = []
        async with aiohttp.ClientSession() as session:
            for text in texts:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent?key={settings.GEMINI_API_KEY}"

                payload = {
                    "content": {
                        "parts": [{"text": text}]
                    }
                }

                async with session.post(url, json=payload) as resp:
                    if resp.status != 200:
                        logger.warning(f"Gemini embedding failed, falling back to OpenAI")
                        return await self._embed_openai(texts, model)

                    result = await resp.json()
                    vector = result.get("embedding", {}).get("values", [])
                    vectors.append(vector)

        return vectors

    async def _embed_clip_texts(self, texts: List[str]) -> List[List[float]]:
        """使用CLIP进行文本向量化"""
        try:
            import torch
            from transformers import CLIPTokenizer, CLIPModel

            # 加载模型
            model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            tokenizer = CLIPTokenizer.from_pretrained("openai/clip-vit-base-patch32")

            # 编码
            inputs = tokenizer(texts, return_tensors="pt", padding=True, truncation=True)
            with torch.no_grad():
                outputs = model.get_text_features(**inputs)

            # 归一化
            embeddings = outputs / outputs.norm(p=2, dim=-1, keepdim=True)

            return embeddings.numpy().tolist()

        except ImportError:
            raise ValueError("CLIP not installed. Install: pip install transformers torch")

    async def _embed_clip_images(self, image_paths: List[str]) -> List[List[float]]:
        """使用CLIP进行图像向量化"""
        try:
            import torch
            from transformers import CLIPProcessor, CLIPModel
            from PIL import Image

            # 加载模型
            model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

            # 加载图片
            images = [Image.open(path).convert("RGB") for path in image_paths]

            # 编码
            inputs = processor(images=images, return_tensors="pt")
            with torch.no_grad():
                outputs = model.get_image_features(**inputs)

            # 归一化
            embeddings = outputs / outputs.norm(p=2, dim=-1, keepdim=True)

            return embeddings.numpy().tolist()

        except ImportError:
            raise ValueError("CLIP not installed. Install: pip install transformers torch pillow")


embedding_service = EmbeddingService()
