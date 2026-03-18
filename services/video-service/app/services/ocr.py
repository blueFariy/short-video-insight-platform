"""
OCR Service - Optical Character Recognition
Support: EasyOCR, Tesseract, 百度OCR, 腾讯OCR
"""
import asyncio
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger

from app.core.config import settings


class OCRProvider:
    """OCR提供商枚举"""
    EASYOCR = "easyocr"
    TESSERACT = "tesseract"
    BAIDU = "baidu"
    TENCENT = "tencent"


class OCRService:
    """文字识别服务"""

    def __init__(self):
        self.temp_dir = Path(settings.VIDEO_TEMP_DIR)

    async def recognize_from_frames(
        self,
        frame_paths: List[str],
        provider: str = "easyocr",
        languages: List[str] = ["zh-cn", "en"]
    ) -> Dict[str, Any]:
        """
        从关键帧识别文字

        Args:
            frame_paths: 关键帧路径列表
            provider: OCR提供商
            languages: 语言列表

        Returns:
            OCR结果
        """
        logger.info(f"OCR processing {len(frame_paths)} frames, provider={provider}")

        all_results = []

        for frame_path in frame_paths:
            result = await self.recognize_from_image(frame_path, provider, languages)
            all_results.append({
                "frame": frame_path,
                "text": result["text"],
                "boxes": result.get("boxes", []),
                "confidence": result.get("confidence", 0)
            })

        # 合并所有文字
        combined_text = " ".join([r["text"] for r in all_results if r["text"]])

        return {
            "provider": provider,
            "frames": all_results,
            "combined_text": combined_text,
            "total_frames": len(frame_paths),
            "frames_with_text": sum(1 for r in all_results if r["text"])
        }

    async def recognize_from_image(
        self,
        image_path: str,
        provider: str = "easyocr",
        languages: List[str] = ["zh-cn", "en"]
    ) -> Dict[str, Any]:
        """
        从单张图片识别文字

        Args:
            image_path: 图片路径
            provider: OCR提供商
            languages: 语言列表

        Returns:
            识别结果
        """
        if provider == OCRProvider.EASYOCR:
            return await self._recognize_easyocr(image_path, languages)
        elif provider == OCRProvider.TESSERACT:
            return await self._recognize_tesseract(image_path)
        elif provider == OCRProvider.BAIDU:
            return await self._recognize_baidu(image_path)
        elif provider == OCRProvider.TENCENT:
            return await self._recognize_tencent(image_path)
        else:
            return await self._recognize_easyocr(image_path, languages)

    async def _recognize_easyocr(
        self,
        image_path: str,
        languages: List[str]
    ) -> Dict[str, Any]:
        """使用EasyOCR进行识别"""
        try:
            import easyocr

            # 初始化reader (首次调用会比较慢)
            reader = easyocr.Reader(languages, gpu=False, verbose=False)

            # 识别
            results = reader.readtext(image_path)

            # 解析结果
            text_parts = []
            boxes = []
            confidences = []

            for bbox, text, confidence in results:
                if text.strip():
                    text_parts.append(text)
                    boxes.append({
                        "text": text,
                        "bbox": bbox,
                        "confidence": confidence
                    })
                    confidences.append(confidence)

            combined_text = " ".join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            return {
                "provider": OCRProvider.EASYOCR,
                "text": combined_text,
                "boxes": boxes,
                "confidence": avg_confidence
            }

        except ImportError:
            logger.warning("EasyOCR not installed, trying tesseract")
            return await self._recognize_tesseract(image_path)

    async def _recognize_tesseract(self, image_path: str) -> Dict[str, Any]:
        """使用Tesseract进行识别"""
        try:
            import pytesseract
            from PIL import Image

            # 打开图片
            image = Image.open(image_path)

            # 识别文字
            text = pytesseract.image_to_string(image, lang="chi_sim+eng")

            # 获取详细数据
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

            # 解析boxes
            boxes = []
            for i, (text_val, conf) in enumerate(zip(data["text"], data["conf"])):
                if text_val.strip() and int(conf) > 0:
                    boxes.append({
                        "text": text_val,
                        "confidence": float(conf) / 100,
                        "bbox": [
                            data["left"][i],
                            data["top"][i],
                            data["left"][i] + data["width"][i],
                            data["top"][i] + data["height"][i]
                        ]
                    })

            # 计算平均置信度
            confidences = [b["confidence"] for b in boxes]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            return {
                "provider": OCRProvider.TESSERACT,
                "text": text.strip(),
                "boxes": boxes,
                "confidence": avg_confidence
            }

        except Exception as e:
            logger.error(f"Tesseract recognition failed: {e}")
            return {
                "provider": OCRProvider.TESSERACT,
                "text": "",
                "boxes": [],
                "confidence": 0,
                "error": str(e)
            }

    async def _recognize_baidu(self, image_path: str) -> Dict[str, Any]:
        """使用百度OCR进行识别"""
        logger.info("Using Baidu OCR")

        # 参考实现
        # from aip import AipOcr
        # client = AipOcr(APP_ID, API_KEY, SECRET_KEY)
        # with open(image_path, 'rb') as f:
        #     result = client.basicGeneral(f.read())

        # 暂时不支持
        return await self._recognize_easyocr(image_path, ["zh-cn", "en"])

    async def _recognize_tencent(self, image_path: str) -> Dict[str, Any]:
        """使用腾讯OCR进行识别"""
        logger.info("Using Tencent OCR")

        # 参考实现
        # from tencentcloud.ocr.v20190619 import OcrClient, models
        # client = OcrClient(cred, "ap-guangzhou")
        # req = models.ImageCorrectOCRRequest()
        # ...

        # 暂时不支持
        return await self._recognize_easyocr(image_path, ["zh-cn", "en"])

    async def detect_text_regions(
        self,
        image_path: str,
        provider: str = "easyocr"
    ) -> List[Dict[str, Any]]:
        """
        检测文字区域（不识别文字内容）

        Args:
            image_path: 图片路径
            provider: OCR提供商

        Returns:
            文字区域列表
        """
        result = await self.recognize_from_image(image_path, provider)
        return result.get("boxes", [])


ocr_service = OCRService()
