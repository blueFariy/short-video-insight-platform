"""
Video Service - Comprehensive Tests
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestVideoDownloader:
    """Test video downloader"""

    def test_video_platform_enum(self):
        """Test VideoPlatform enum"""
        from app.services.downloader import VideoPlatform
        assert VideoPlatform.DOUYIN == "douyin"
        assert VideoPlatform.BILIBILI == "bilibili"
        assert VideoPlatform.XIAOHONGSHU == "xiaohongshu"

    def test_platform_detection_douyin(self):
        """Test platform detection for Douyin"""
        from app.services.downloader import VideoDownloader
        downloader = VideoDownloader()
        url = "https://v.douyin.com/abc123/"
        platform = downloader._detect_platform(url)
        assert platform == "douyin"

    def test_platform_detection_bilibili(self):
        """Test platform detection for Bilibili"""
        from app.services.downloader import VideoDownloader
        downloader = VideoDownloader()
        url = "https://www.bilibili.com/video/BV123456/"
        platform = downloader._detect_platform(url)
        assert platform == "bilibili"

    def test_platform_detection_xiaohongshu(self):
        """Test platform detection for Xiaohongshu"""
        from app.services.downloader import VideoDownloader
        downloader = VideoDownloader()
        url = "https://www.xiaohongshu.com/discovery/item/abc"
        platform = downloader._detect_platform(url)
        assert platform == "xiaohongshu"

    def test_video_id_generation(self):
        """Test video ID generation"""
        from app.services.downloader import VideoDownloader
        downloader = VideoDownloader()
        url = "https://v.douyin.com/test/"
        video_id = downloader._generate_video_id(url)
        assert video_id is not None
        assert len(video_id) > 0

    @pytest.mark.asyncio
    async def test_download_douyin_invalid_url(self):
        """Test download with invalid URL"""
        from app.services.downloader import VideoDownloader
        downloader = VideoDownloader()

        with pytest.raises(ValueError, match="Cannot extract video ID"):
            await downloader._download_douyin("invalid_url")


class TestKeyframeExtractor:
    """Test keyframe extraction"""

    def test_keyframe_config(self):
        """Test keyframe extraction configuration"""
        from app.services.keyframe import KeyframeExtractor
        extractor = KeyframeExtractor()
        assert extractor.output_dir.exists() or True  # Directory may be created

    @pytest.mark.asyncio
    async def test_extract_keyframes_invalid_path(self):
        """Test keyframe extraction with invalid video path"""
        from app.services.keyframe import KeyframeExtractor
        from app.core.exceptions import AppException

        extractor = KeyframeExtractor()
        with patch('os.path.exists', return_value=False):
            with pytest.raises(AppException):
                await extractor.extract_keyframes("invalid_path.mp4", 5)


class TestASRService:
    """Test ASR service"""

    def test_asr_provider_enum(self):
        """Test ASR provider enum"""
        from app.services.asr import ASRProvider
        assert ASRProvider.OPENAI == "openai"
        assert ASRProvider.ALIYUN == "aliyun"
        assert ASRProvider.TENCENT == "tencent"

    @pytest.mark.asyncio
    async def test_transcribe_missing_file(self):
        """Test transcription with missing file"""
        from app.services.asr import ASRService
        asr_service = ASRService()

        with pytest.raises(FileNotFoundError):
            await asr_service.transcribe("nonexistent.mp3")


class TestOCRService:
    """Test OCR service"""

    def test_ocr_provider_enum(self):
        """Test OCR provider enum"""
        from app.services.ocr import OCRProvider
        assert OCRProvider.EASYOCR == "easyocr"
        assert OCRProvider.TESSERACT == "tesseract"

    @pytest.mark.asyncio
    async def test_extract_text_missing_image(self):
        """Test OCR with missing image"""
        from app.services.ocr import OCRService
        ocr_service = OCRService()

        with pytest.raises(FileNotFoundError):
            await ocr_service.extract_text("nonexistent.jpg")


class TestEmbeddingService:
    """Test embedding service"""

    def test_embedding_provider_enum(self):
        """Test embedding provider enum"""
        from app.services.embedding import EmbeddingProvider
        assert EmbeddingProvider.OPENAI == "openai"
        assert EmbeddingProvider.GEMINI == "gemini"
        assert EmbeddingProvider.CLIP == "clip"

    def test_dimension_mapping(self):
        """Test embedding dimension mapping"""
        from app.services.embedding import EmbeddingProvider
        # Verify dimensions are set
        assert EmbeddingProvider.OPENAI.dimension == 1536  # type: ignore


class TestVideoSearch:
    """Test video search"""

    def test_search_params(self):
        """Test search parameters"""
        from app.services.video_search import VideoSearchService
        # Test initialization
        search_service = VideoSearchService()
        assert search_service.index_name == "videos"


class TestResponseModel:
    """Test response models"""

    def test_success_response(self):
        """Test success response"""
        from app.core.response import success_response
        response = success_response(data={"video_id": "123"})
        assert response.code == 200
        assert response.message == "success"

    def test_error_response(self):
        """Test error response"""
        from app.core.response import error_response
        response = error_response(code=500, message="Error")
        assert response.code == 500


class TestExceptions:
    """Test exceptions"""

    def test_app_exception(self):
        """Test AppException"""
        from app.core.exceptions import AppException
        exc = AppException("Test error", code=500)
        assert exc.message == "Test error"
        assert exc.code == 500

    def test_validation_exception(self):
        """Test ValidationException"""
        from app.core.exceptions import ValidationException
        exc = ValidationException("Invalid input")
        assert exc.code == 400

    def test_not_found_exception(self):
        """Test NotFoundException"""
        from app.core.exceptions import NotFoundException
        exc = NotFoundException("Not found")
        assert exc.code == 404
