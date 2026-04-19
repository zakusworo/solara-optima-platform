"""
Core configuration and settings for Solar UC/ED Platform
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable overrides"""
    
    # Application
    APP_NAME: str = "Solara Optima Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Location (Default: Bandung, Indonesia)
    LATITUDE: float = -6.9147
    LONGITUDE: float = 107.6098
    ALTITUDE: float = 768
    TIMEZONE: str = "Asia/Jakarta"
    HEMISPHERE: str = "southern"
    OPTIMAL_AZIMUTH: float = 0.0  # North-facing for southern hemisphere
    
    # Market Settings
    CURRENCY: str = "IDR"
    USD_IDR_RATE: float = 15500.0
    CARBON_PRICE: float = 50000.0  # Rp/tCO2
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/solar_uc_ed"
    DATABASE_ECHO: bool = False
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Ollama AI
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3.5"
    FORECAST_MODEL: str = "qwen3.5"
    
    # Optimization
    SOLVER_NAME: str = "cbc"  # Options: cbc, glpk, gurobi, cplex
    SOLVER_TIME_LIMIT: int = 300  # seconds
    OPTIMIZATION_HORIZON: int = 24  # hours
    TIME_RESOLUTION: int = 1  # hours
    
    # Solar PV Defaults
    PV_SYSTEM_CAPACITY: float = 100.0  # kW
    PV_MODULE_EFFICIENCY: float = 0.20
    PV_INVERTER_EFFICIENCY: float = 0.96
    PV_TILT_ANGLE: Optional[float] = None  # Auto-calculate from latitude
    PV_AZIMUTH: float = 0.0  # North-facing
    PV_LOSS_FACTOR: float = 0.14  # System losses
    
    # Battery Storage Defaults
    BESS_CAPACITY: float = 50.0  # kWh
    BESS_POWER_RATING: float = 25.0  # kW
    BESS_EFFICIENCY: float = 0.90
    BESS_MIN_SOC: float = 0.10
    BESS_MAX_SOC: float = 0.90
    BESS_DEGRADATION_COST: float = 100.0  # Rp/kWh throughput
    
    # Reserve Requirements
    SPINNING_RESERVE_PCT: float = 10.0
    OPERATING_RESERVE_PCT: float = 15.0
    LOAD_UNCERTAINTY_PCT: float = 5.0
    
    # File Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    WEATHER_DIR: Path = DATA_DIR / "weather"
    LOAD_PROFILES_DIR: Path = DATA_DIR / "load_profiles"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance for dependency injection"""
    return settings
