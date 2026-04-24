"""
Forecasting API endpoints - Solar and Load predictions
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict
from datetime import datetime, timedelta
from loguru import logger

from app.models.schemas import (
    SolarForecastResponse,
    LoadForecastResponse,
    ForecastRequest,
    APIResponse,
)
from app.services.solar_forecast import SolarForecastService, generate_solar_forecast
from app.core.config import settings

router = APIRouter()


@router.get("/solar", response_model=APIResponse)
async def get_solar_forecast(
    capacity: float = Query(..., description="PV system capacity (kW)"),
    hours: int = Query(default=24, ge=1, le=168, description="Forecast horizon (hours)"),
    latitude: Optional[float] = Query(None, description="Override latitude"),
    longitude: Optional[float] = Query(None, description="Override longitude"),
    altitude: Optional[float] = Query(None, description="Override altitude (m)"),
    tilt: Optional[float] = Query(None, description="Panel tilt angle"),
    azimuth: Optional[float] = Query(None, description="Panel azimuth (0°=North)"),
):
    """
    Generate solar PV generation forecast
    
    Uses pvlib with location-specific weather data.
    Default location: Bandung, Indonesia (-6.9147°S, 107.6098°E)
    
    For southern hemisphere: optimal azimuth is 0° (North-facing)
    """
    try:
        logger.info(f"Generating solar forecast: {capacity}kW, {hours}h horizon")
        
        # Use custom location if provided
        location = None
        if latitude is not None and longitude is not None:
            location = {
                'latitude': latitude,
                'longitude': longitude,
                'altitude': settings.ALTITUDE if altitude is None else altitude,
            }
        
        # Generate forecast
        forecast = await generate_solar_forecast(
            capacity=capacity,
            horizon_hours=hours,
            location=location,
        )
        
        # Apply custom tilt/azimuth if provided
        if tilt is not None or azimuth is not None:
            service = SolarForecastService(
                latitude=latitude,
                longitude=longitude,
            )
            forecast_data = service.generate_forecast(
                capacity=capacity,
                horizon_hours=hours,
                tilt=tilt,
                azimuth=azimuth or settings.OPTIMAL_AZIMUTH,
            )
            forecast.generation = forecast_data['generation']
            forecast.total_generation = forecast_data['total_generation']
        
        logger.info(
            f"Solar forecast: {forecast.total_generation:.1f} kWh total, "
            f"peak: {max(forecast.generation)/1000:.2f} kW"
        )
        
        return APIResponse(
            success=True,
            data=forecast.model_dump(),
            message=f"Solar forecast generated for {capacity}kW system",
        )
        
    except Exception as e:
        logger.error(f"Solar forecasting failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/load", response_model=APIResponse)
async def get_load_forecast(
    hours: int = Query(default=24, ge=1, le=168, description="Forecast horizon (hours)"),
    profile_type: str = Query(default="commercial", description="Load profile type"),
    scale: float = Query(default=1.0, ge=0, description="Load scaling factor"),
):
    """
    Generate load forecast using typical profiles
    
    Profile types:
    - residential: Typical household load
    - commercial: Office/commercial building
    - industrial: Industrial facility
    - mixed: Mixed use profile
    """
    try:
        logger.info(f"Generating load forecast: {hours}h, type={profile_type}")
        
        # Generate typical load profile
        timestamps = []
        load_values = []
        
        base_load = get_base_load_profile(profile_type)
        
        for h in range(hours):
            timestamp = datetime.now() + timedelta(hours=h)
            timestamps.append(timestamp)
            
            # Scale by hour-of-day profile
            hour_factor = base_load[h % 24]
            load = hour_factor * scale
            
            load_values.append(load)
        
        # Calculate statistics
        peak_load = max(load_values)
        total_energy = sum(load_values)
        
        forecast = LoadForecastResponse(
            timestamps=timestamps,
            load=load_values,
            peak_load=peak_load,
            total_energy=total_energy,
        )
        
        logger.info(f"Load forecast: peak={peak_load:.1f}kW, total={total_energy:.1f}kWh")
        
        return APIResponse(
            success=True,
            data=forecast.model_dump(),
            message=f"Load forecast generated ({profile_type} profile)",
        )
        
    except Exception as e:
        logger.error(f"Load forecasting failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/load/custom", response_model=APIResponse)
async def create_custom_load_forecast(request: ForecastRequest):
    """
    Create custom load forecast from historical data
    
    Uses simple pattern matching and trend extrapolation
    """
    try:
        if not request.historical_data:
            raise HTTPException(status_code=400, detail="Historical data is required")
        
        logger.info(f"Creating custom load forecast from {len(request.historical_data)} data points")
        
        # Simple forecasting: use historical average by hour-of-day
        historical = request.historical_data
        hours_in_day = 24
        
        # Calculate hourly averages
        hourly_avg = []
        for h in range(hours_in_day):
            hour_values = [historical[i] for i in range(h, len(historical), hours_in_day)]
            hourly_avg.append(sum(hour_values) / len(hour_values) if hour_values else 0)
        
        # Generate forecast
        forecast_hours = int((request.end_date - request.start_date).total_seconds() / 3600)
        timestamps = []
        load_values = []
        
        for h in range(forecast_hours):
            timestamp = request.start_date + timedelta(hours=h)
            timestamps.append(timestamp)
            load_values.append(hourly_avg[h % 24])
        
        forecast = LoadForecastResponse(
            timestamps=timestamps,
            load=load_values,
            peak_load=max(load_values),
            total_energy=sum(load_values),
        )
        
        return APIResponse(
            success=True,
            data=forecast.model_dump(),
            message="Custom load forecast generated",
        )
        
    except Exception as e:
        logger.error(f"Custom load forecast failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def get_base_load_profile(profile_type: str) -> list:
    """Get typical load profile by type (24-hour factors)"""
    
    profiles = {
        'residential': [
            0.5, 0.4, 0.4, 0.4, 0.5, 0.7,  # 00-05
            0.9, 1.0, 0.9, 0.8, 0.8, 0.9,  # 06-11
            1.0, 0.9, 0.9, 1.0, 1.1, 1.2,  # 12-17
            1.3, 1.4, 1.2, 1.0, 0.8, 0.6,  # 18-23
        ],
        'commercial': [
            0.3, 0.3, 0.3, 0.3, 0.4, 0.5,  # 00-05
            0.7, 0.9, 1.0, 1.0, 1.0, 0.9,  # 06-11
            0.9, 1.0, 1.0, 1.0, 0.9, 0.8,  # 12-17
            0.6, 0.5, 0.4, 0.4, 0.3, 0.3,  # 18-23
        ],
        'industrial': [
            0.8, 0.8, 0.8, 0.8, 0.8, 0.9,  # 00-05
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0,  # 06-11
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0,  # 12-17
            1.0, 1.0, 0.9, 0.9, 0.8, 0.8,  # 18-23
        ],
        'mixed': [
            0.4, 0.4, 0.4, 0.4, 0.5, 0.6,  # 00-05
            0.8, 0.9, 1.0, 0.9, 0.9, 0.9,  # 06-11
            1.0, 0.9, 0.9, 1.0, 1.0, 1.0,  # 12-17
            1.1, 1.2, 1.1, 0.9, 0.7, 0.5,  # 18-23
        ],
    }
    
    return profiles.get(profile_type, profiles['mixed'])


@router.get("/compare")
async def compare_scenarios(
    capacity: float = Query(..., description="PV capacity (kW)"),
    hours: int = Query(default=24, description="Hours"),
):
    """Compare solar generation with and without optimal tilt"""
    
    service = SolarForecastService()
    
    # Standard forecast (auto tilt)
    forecast_standard = service.generate_forecast(
        capacity=capacity,
        horizon_hours=hours,
    )
    
    # Fixed tilt (suboptimal)
    forecast_fixed = service.generate_forecast(
        capacity=capacity,
        horizon_hours=hours,
        tilt=10,  # Flat installation
        azimuth=180,  # South-facing (wrong for southern hemisphere!)
    )
    
    improvement = (
        (forecast_standard['total_generation'] - forecast_fixed['total_generation']) /
        forecast_fixed['total_generation'] * 100
    )
    
    return APIResponse(
        success=True,
        data={
            'optimal': {
                'tilt': service.get_optimal_tilt(),
                'azimuth': settings.OPTIMAL_AZIMUTH,
                'total_generation': forecast_standard['total_generation'],
            },
            'suboptimal': {
                'tilt': 10,
                'azimuth': 180,
                'total_generation': forecast_fixed['total_generation'],
            },
            'improvement_percent': improvement,
        },
        message=f"Optimal tilt improves generation by {improvement:.1f}%",
    )
