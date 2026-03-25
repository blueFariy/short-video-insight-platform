"""
Data Collector Service - Main Entry Point
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.handlers import (
    app_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.api.v1.router import api_router


# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    logger.info(f"{settings.SERVICE_NAME} starting up...")

    # Initialize database
    from app.models import db_manager
    try:
        db_manager.init_db()
        await db_manager.create_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    # Start scheduler
    from app.services.scheduler_service import scheduler_service

    # Add default collection task
    await scheduler_service.add_task(
        task_id="auto_collect",
        name="自动采集任务",
        func=lambda: None,  # Demo task
        interval=settings.COLLECTION_INTERVAL,
        enabled=False  # Disabled by default
    )

    await scheduler_service.start()

    yield

    # Stop scheduler
    await scheduler_service.stop()
    # Close database connection
    await db_manager.close()
    logger.info(f"{settings.SERVICE_NAME} shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Data Collector Service",
    description="Competitor content collection and monitoring service",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(api_router, prefix="/api/v1")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from app.services.scheduler_service import scheduler_service
    scheduler_status = await scheduler_service.get_status()

    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "scheduler": scheduler_status
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=True
    )