"""
Main FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from app.core.config import settings
from app.api import optimize, forecast, generators, weather, ai_forecast, location
from app.core.logging import setup_logging


def create_application() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Setup logging
    setup_logging()
    
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Unit Commitment & Economic Dispatch Optimization with Renewable Integration",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    application.include_router(optimize.router, prefix="/api/v1/optimize", tags=["Optimization"])
    application.include_router(forecast.router, prefix="/api/v1/forecast", tags=["Forecasting"])
    application.include_router(generators.router, prefix="/api/v1/generators", tags=["Generators"])
    application.include_router(weather.router, prefix="/api/v1/weather", tags=["Weather"])
    application.include_router(ai_forecast.router, prefix="/api/v1/ai", tags=["AI Forecasting"])
    application.include_router(location.router, prefix="/api/v1/location", tags=["Location"])
    
    @application.get("/")
    async def root():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "location": {
                "latitude": settings.LATITUDE,
                "longitude": settings.LONGITUDE,
                "timezone": settings.TIMEZONE,
            }
        }
    
    @application.get("/health")
    async def health_check():
        """Detailed health check"""
        return {
            "status": "ok",
            "services": {
                "api": "running",
                "optimization": "ready",
                "forecasting": "ready",
            }
        }
    
    @application.on_event("startup")
    async def startup_event():
        """Initialize on startup"""
        logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
        logger.info(f"Location: Bandung ({settings.LATITUDE}, {settings.LONGITUDE})")
        logger.info(f"Solver: {settings.SOLVER_NAME}")
        
        # Ensure data directories exist
        settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
        settings.WEATHER_DIR.mkdir(parents=True, exist_ok=True)
        settings.LOAD_PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    
    @application.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown"""
        logger.info("Shutting down application")
    
    return application


app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
