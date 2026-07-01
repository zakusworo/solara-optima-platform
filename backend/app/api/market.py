"""
Market rates API — live USD/IDR and carbon price with fallback.
"""

import asyncio

from fastapi import APIRouter
from loguru import logger

from app.models.schemas import APIResponse
from app.services.market_rates import market_rates_service

router = APIRouter()


@router.get("/rates", response_model=APIResponse)
async def get_rates():
    """Current market rates (live if fetched, otherwise config fallback)."""
    return APIResponse(
        success=True,
        data=market_rates_service.get(),
        message="Market rates",
    )


@router.post("/rates/refresh", response_model=APIResponse)
async def refresh_rates():
    """Force a re-fetch of live market rates."""
    logger.info("Manual market-rates refresh requested")
    data = await asyncio.to_thread(market_rates_service.refresh)
    return APIResponse(success=True, data=data, message="Market rates refreshed")
