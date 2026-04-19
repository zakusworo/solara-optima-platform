"""
Weather API endpoints - Access weather data for solar forecasting
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta
from loguru import logger

from app.models.schemas import WeatherData, APIResponse
from app.services.solar_forecast import SolarForecastService
from app.core.config import settings

router = APIRouter()


@router.get("/current", response_model=APIResponse)
async def get_current_weather():
    """
    Get current weather conditions for Bandung
    
    Returns typical values for the region (placeholder for real API integration)
    """
    
    # Placeholder - integrate with OpenWeatherMap or BMKG API
    now = datetime.now()
    
    weather = {
        'timestamp': now.isoformat(),
        'location': {
            'latitude': settings.LATITUDE,
            'longitude': settings.LONGITUDE,
            'altitude': settings.ALTITUDE,
        },
        'ghi': 800,  # W/m²
        'dhi': 150,
        'dni': 650,
        'temperature': 28,  # °C
        'humidity': 75,  # %
        'wind_speed': 2.5,  # m/s
        'cloud_cover': 30,  # %
    }
    
    return APIResponse(
        success=True,
        data=weather,
        message="Current weather data for Bandung",
    )


@router.get("/forecast", response_model=APIResponse)
async def get_weather_forecast(
    hours: int = Query(default=24, ge=1, le=168, description="Forecast horizon"),
):
    """
    Get weather forecast for solar generation modeling
    
    Integrates with weather APIs for GHI, DNI, DHI, temperature
    """
    
    logger.info(f"Generating weather forecast for {hours} hours")
    
    # Generate synthetic forecast (replace with real API)
    service = SolarForecastService()
    weather = service.get_weather_data(
        start=datetime.now(),
        end=datetime.now() + timedelta(hours=hours),
        source='clearsky',
    )
    
    forecast_data = {
        'timestamps': [ts.isoformat() for ts in weather.index],
        'ghi': weather['ghi'].tolist(),
        'dhi': weather['dhi'].tolist(),
        'dni': weather['dni'].tolist(),
        'temperature': weather['temp_air'].tolist(),
        'wind_speed': weather['wind_speed'].tolist(),
    }
    
    return APIResponse(
        success=True,
        data=forecast_data,
        message=f"Weather forecast for {hours} hours",
    )


@router.get("/tmy", response_model=APIResponse)
async def get_tmy_data(
    month: Optional[int] = Query(None, ge=1, le=12, description="Specific month"),
):
    """
    Get Typical Meteorological Year (TMY) data for Bandung
    
    TMY data represents long-term average weather conditions
    """
    
    tmy_file = settings.WEATHER_DIR / "bandung_tmy.csv"
    
    if not tmy_file.exists():
        # Generate synthetic TMY
        logger.info("TMY file not found, generating synthetic data")
        service = SolarForecastService()
        
        # Generate full year
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31, 23, 0)
        
        weather = service.get_weather_data(start, end, source='clearsky')
        
        # Save for future use
        weather.to_csv(tmy_file)
        logger.info(f"TMY data saved to {tmy_file}")
    
    # Read TMY data
    try:
        tmy = pd.read_csv(tmy_file, index_col=0, parse_dates=True)
        
        if month:
            tmy = tmy[tmy.index.month == month]
        
        return APIResponse(
            success=True,
            data={
                'records': len(tmy),
                'period': f"{tmy.index[0].isoformat()} to {tmy.index[-1].isoformat()}",
                'avg_ghi': tmy['ghi'].mean(),
                'avg_temperature': tmy['temp_air'].mean(),
            },
            message="TMY data retrieved",
        )
        
    except Exception as e:
        logger.error(f"TMY data error: {str(e)}")
        raise HTTPException(status_code=500, detail="TMY data unavailable")


@router.get("/solar-resource", response_model=APIResponse)
async def get_solar_resource():
    """
    Get solar resource assessment for Bandung location
    
    Includes:
    - Annual solar irradiation
    - Monthly averages
    - Optimal tilt angles
    """
    
    service = SolarForecastService()
    
    # Calculate solar resource metrics
    optimal_tilt = service.get_optimal_tilt()
    
    # Typical values for Bandung (tropical highland)
    solar_resource = {
        'location': {
            'latitude': settings.LATITUDE,
            'longitude': settings.LONGITUDE,
            'altitude': settings.ALTITUDE,
            'timezone': settings.TIMEZONE,
        },
        'annual_irradiation': 1650,  # kWh/m²/year
        'monthly_averages': [
            {'month': 1, 'ghi': 4.8, 'temp': 24},
            {'month': 2, 'ghi': 4.9, 'temp': 24},
            {'month': 3, 'ghi': 5.0, 'temp': 25},
            {'month': 4, 'ghi': 5.1, 'temp': 25},
            {'month': 5, 'ghi': 4.9, 'temp': 25},
            {'month': 6, 'ghi': 4.7, 'temp': 24},
            {'month': 7, 'ghi': 4.8, 'temp': 24},
            {'month': 8, 'ghi': 5.0, 'temp': 25},
            {'month': 9, 'ghi': 5.2, 'temp': 26},
            {'month': 10, 'ghi': 5.3, 'temp': 26},
            {'month': 11, 'ghi': 5.0, 'temp': 25},
            {'month': 12, 'ghi': 4.7, 'temp': 24},
        ],
        'optimal_tilt': {
            'year_round': optimal_tilt,
            'wet_season': service.get_optimal_tilt(1),  # Nov-Mar
            'dry_season': service.get_optimal_tilt(6),  # Apr-Oct
        },
        'optimal_azimuth': settings.OPTIMAL_AZIMUTH,  # 0° = North
        'capacity_factor_estimate': 0.16,  # Typical for tropical
    }
    
    return APIResponse(
        success=True,
        data=solar_resource,
        message="Solar resource assessment for Bandung",
    )


# Import pandas here to avoid circular imports
import pandas as pd
