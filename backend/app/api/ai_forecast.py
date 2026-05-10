"""
AI Forecasting API endpoints
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.models.schemas import APIResponse
from app.services.ai_forecast import AIForecastingService, generate_ai_load_forecast

# Hard caps on the comma-separated forecast input to prevent DoS via
# huge query strings or excessively long forecast horizons.
_MAX_FORECAST_INPUT_CHARS = 8_192
_MAX_FORECAST_VALUES = 168  # one week of hourly data

router = APIRouter()


@router.get("/ai/load", response_model=APIResponse)
async def get_ai_load_forecast(
    hours: int = 24,
    model: Optional[str] = None,
):
    """
    Generate load forecast using AI/LLM

    Uses Ollama with pattern recognition on historical data.
    Falls back to statistical methods if Ollama unavailable.
    """
    try:
        logger.info(
            f"Generating AI load forecast: {hours}h, model={model or 'default'}"
        )

        # WARNING: this endpoint feeds the model SYNTHETIC historical data
        # (no real meter feed wired up). Every response is flagged with
        # data_source="synthetic" so callers don't mistake it for production
        # forecasts. Use POST /ai/load/custom to supply real historical data.
        historical = generate_synthetic_load_data(days=7)

        service = AIForecastingService(model=model)

        if not service.check_availability():
            return APIResponse(
                success=True,
                data={
                    "forecast": (
                        historical[-hours:] if len(historical) >= hours else historical
                    ),
                    "confidence": 0.5,
                    "method": "Fallback (Ollama unavailable)",
                    "model": "statistical",
                    "data_source": "synthetic",
                },
                message=(
                    "Ollama not available — returning synthetic fallback. "
                    "Use POST /ai/load/custom with real historical data for production use."
                ),
            )

        result = service.generate_load_forecast(historical, hours)
        result["data_source"] = "synthetic"

        return APIResponse(
            success=True,
            data=result,
            message=(
                f"AI forecast generated with {result['model']} from SYNTHETIC input — "
                "use POST /ai/load/custom with real data for production use"
            ),
        )

    except Exception as e:
        logger.error(f"AI load forecast failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/load/custom", response_model=APIResponse)
async def get_custom_ai_load_forecast(
    historical_data: List[float],
    hours: int = 24,
    context: Optional[Dict] = None,
    model: Optional[str] = None,
):
    """
    Generate load forecast from custom historical data

    Provide your own historical load data for better accuracy.
    """
    try:
        if len(historical_data) < 24:
            raise HTTPException(
                status_code=400,
                detail="At least 24 hours of historical data required",
            )

        logger.info(
            f"Custom AI forecast: {len(historical_data)} data points, {hours}h horizon"
        )

        result = await generate_ai_load_forecast(
            historical_data=historical_data,
            horizon_hours=hours,
            context=context,
            model=model,
        )

        return APIResponse(
            success=True,
            data=result,
            message=f"Custom forecast generated (confidence: {result['confidence']:.2f})",
        )

    except Exception as e:
        logger.error(f"Custom AI forecast failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai/solar/refine", response_model=APIResponse)
async def refine_solar_forecast(
    pvlib_forecast: str = Query(
        ...,
        max_length=_MAX_FORECAST_INPUT_CHARS,
        description="Comma-separated pvlib forecast values (kW)",
    ),
    cloud_cover: Optional[int] = Query(None, ge=0, le=100),
    temperature: Optional[float] = Query(None, ge=-50, le=60),
    model: Optional[str] = Query(None, max_length=64),
):
    """
    Refine pvlib solar forecast using AI weather analysis

    Adjusts base pvlib forecast based on cloud cover and temperature.
    """
    try:
        # Parse pvlib forecast with bounds enforcement
        try:
            forecast_values = [
                float(x.strip()) for x in pvlib_forecast.split(",") if x.strip()
            ]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="pvlib_forecast must contain only numeric values",
            )
        if not forecast_values:
            raise HTTPException(status_code=400, detail="pvlib_forecast is empty")
        if len(forecast_values) > _MAX_FORECAST_VALUES:
            raise HTTPException(
                status_code=400,
                detail=f"pvlib_forecast exceeds max {_MAX_FORECAST_VALUES} values",
            )

        # Build weather context
        weather = {}
        if cloud_cover is not None:
            weather["cloud_cover"] = cloud_cover
        if temperature is not None:
            weather["temperature"] = temperature

        logger.info(f"Refining solar forecast with AI: {len(forecast_values)} values")

        service = AIForecastingService(model=model)
        result = service.generate_solar_forecast_refinement(forecast_values, weather)

        return APIResponse(
            success=True,
            data=result,
            message="Solar forecast refined with AI weather analysis",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Solar refinement failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai/compare", response_model=APIResponse)
async def compare_forecasting_methods(
    hours: int = 24,
):
    """
    Compare AI forecasting with traditional methods

    Shows differences between:
    - AI/LLM pattern recognition
    - Simple average
    - Hour-of-day averaging
    """
    try:
        logger.info("Comparing forecasting methods")

        # NOTE: synthetic input data — comparison shows method differences,
        # not absolute accuracy on real meter data.
        historical = generate_synthetic_load_data(days=7)

        service = AIForecastingService()

        if not service.check_availability():
            return APIResponse(
                success=True,
                data={
                    "error": "Ollama not available",
                    "fallback_only": True,
                    "data_source": "synthetic",
                },
                message="Cannot compare: Ollama unavailable",
            )

        comparison = service.compare_forecasting_methods(historical, hours)
        if isinstance(comparison, dict):
            comparison["data_source"] = "synthetic"

        return APIResponse(
            success=True,
            data=comparison,
            message="Forecasting methods compared on SYNTHETIC input data",
        )

    except Exception as e:
        logger.error(f"Method comparison failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai/status", response_model=APIResponse)
async def get_ai_status():
    """Check AI forecasting service status"""

    service = AIForecastingService()
    available = service.check_availability()

    return APIResponse(
        success=True,
        data={
            "ollama_available": available,
            "model": service.model,
            "host": service.host,
            "capabilities": (
                [
                    "Load forecasting",
                    "Solar forecast refinement",
                    "Method comparison",
                ]
                if available
                else []
            ),
        },
        message="AI service ready" if available else "Ollama not available",
    )


def generate_synthetic_load_data(days: int = 7) -> List[float]:
    """Generate synthetic load data for testing"""
    import numpy as np

    hours = days * 24
    load = []

    for h in range(hours):
        # Base load with daily pattern
        hour_of_day = h % 24

        # Typical tropical commercial load profile
        if 0 <= hour_of_day < 6:
            base = 60 + np.random.normal(0, 5)
        elif 6 <= hour_of_day < 9:
            base = 80 + np.random.normal(0, 8)
        elif 9 <= hour_of_day < 12:
            base = 120 + np.random.normal(0, 10)
        elif 12 <= hour_of_day < 14:
            base = 100 + np.random.normal(0, 8)  # Lunch dip
        elif 14 <= hour_of_day < 18:
            base = 130 + np.random.normal(0, 10)
        elif 18 <= hour_of_day < 21:
            base = 110 + np.random.normal(0, 8)
        else:
            base = 70 + np.random.normal(0, 5)

        # Add weekly pattern (lower on weekends)
        day_of_week = h // 24
        if day_of_week % 7 >= 5:  # Weekend
            base *= 0.7

        load.append(max(0, base))

    return load
