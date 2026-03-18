"""
Video Service - Main Application Entry
"""
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.core.logging import init_logging
from app.core.handlers import register_exception_handlers
from app.core.elasticsearch_client import es_manager
from app.middleware import RequestIDMiddleware, LoggingMiddleware
from app.api.v1 import api_router

# Initialize logging
init_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("Video Service starting up...")

    # Initialize Elasticsearch
    try:
        await es_manager.init_elasticsearch()
        logger.info("Elasticsearch initialized")

        # 创建视频索引
        from app.services.video_search import video_search_service
        video_search_service.es_client = es_manager.client
        await video_search_service.create_index()
    except Exception as e:
        logger.warning(f"Elasticsearch initialization failed: {e}")

    # 创建下载目录
    Path(settings.VIDEO_DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.VIDEO_TEMP_DIR).mkdir(parents=True, exist_ok=True)

    yield

    # Cleanup
    logger.info("Video Service shutting down...")
    await es_manager.close()
    logger.info("All connections closed")


app = FastAPI(
    title="Video Service API",
    description="视频处理服务API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Register exception handlers
register_exception_handlers(app)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "video-service"}


# Include API router
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="localhost",
        port=8002,
        reload=True
    )
