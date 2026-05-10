"""
Logging configuration using Loguru
"""
from loguru import logger
import sys
from app.core.config import settings


def setup_logging():
    """Configure application logging"""
    
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        backtrace=True,
        diagnose=True,
    )
    
    # Add file handler if configured
    if settings.LOG_FILE:
        logger.add(
            settings.LOG_FILE,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=settings.LOG_LEVEL,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
        )
    
    logger.info("Logging configured successfully")
