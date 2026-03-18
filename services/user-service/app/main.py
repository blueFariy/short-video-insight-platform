"""
User Service - Main Application Entry
"""
import os
import sys
from contextlib import asynccontextmanager

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.core.logging import init_logging
from app.core.handlers import register_exception_handlers
from app.core.database import db_manager
from app.core.redis_client import redis_manager
from app.core.elasticsearch_client import es_manager
from app.middleware import RequestIDMiddleware, LoggingMiddleware
from app.api.v1 import api_router


# Initialize logging
init_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("User Service starting up...")

    # Initialize database
    db_manager.init_db()
    logger.info("Database initialized")

    # Initialize Redis
    try:
        await redis_manager.init_redis()
        logger.info("Redis initialized")
    except Exception as e:
        logger.warning(f"Redis initialization failed: {e}")

    # Initialize Elasticsearch
    try:
        await es_manager.init_elasticsearch()
        logger.info("Elasticsearch initialized")
    except Exception as e:
        logger.warning(f"Elasticsearch initialization failed: {e}")

    yield

    # Cleanup
    logger.info("User Service shutting down...")
    await redis_manager.close()
    await es_manager.close()
    await db_manager.close()
    logger.info("All connections closed")


app = FastAPI(
    title="User Service API",
    description="用户服务API",
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
    return {"status": "healthy", "service": "user-service"}


# Include API router
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="localhost",
        port=8001,
        reload=True
    )
