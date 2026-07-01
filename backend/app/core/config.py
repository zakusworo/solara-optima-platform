"""
Core configuration and settings for Solara Optima Platform
"""

from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable overrides"""

    # Application
    APP_NAME: str = "Solara Optima Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS — comma-separated origins (e.g. "http://localhost:3000,https://app.example.com").
    # Use "*" only in DEBUG; in production set explicitly.
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

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

    # Live market rates — fetched at startup, falling back to the values above.
    ENABLE_LIVE_RATES: bool = True
    FX_RATES_URL: str = "https://open.er-api.com/v6/latest/USD"  # free, no API key
    # Optional carbon-price source (JSON with `price_idr_per_tco2` or `price`).
    # None -> keep the CARBON_PRICE default (no free live IDR carbon feed yet).
    CARBON_PRICE_URL: Optional[str] = None
    RATES_TTL_HOURS: int = 6

    # Real irradiance via PVGIS (JRC) — free, no API key. Used by the marketplace
    # yield calc when a site latitude/longitude is supplied; falls back to the
    # clear-sky model when offline/unavailable. TMY is disk-cached per location.
    ENABLE_PVGIS: bool = True
    PVGIS_BASE_URL: str = "https://re.jrc.ec.europa.eu/api/v5_2"
    PVGIS_TTL_DAYS: int = 30  # TMY is stable; refetch monthly
    PVGIS_TIMEOUT_S: int = 8

    # Marketplace leads — stored as append-only JSONL pending a DB migration
    # (see ROADMAP §7). LEADS_ADMIN_TOKEN gates the admin list/export endpoints;
    # leave None to disable admin access entirely (endpoints return 503).
    LEADS_ADMIN_TOKEN: Optional[str] = None
    LEADS_RATE_LIMIT_PER_MIN: int = 5  # per-client quote-request cap

    # Carbon credits (I-REC) — indicative monetisation of rooftop solar via
    # International Renewable Energy Certificates (1 cert = 1 MWh). Surfaced in
    # the marketplace estimate + portfolio for the CIIC carbon-credit framing.
    IREC_PRICE_USD: float = 1.5  # USD per I-REC certificate (indicative, configurable)

    # Database
    DATABASE_URL: str = "postgresql://user:***@localhost:5432/solara_optima"
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
