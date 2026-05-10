"""
Optimization API endpoints
"""

import uuid
from collections import OrderedDict
from datetime import datetime, timedelta
from threading import Lock

from fastapi import APIRouter, HTTPException
from loguru import logger

from app.core.config import settings
from app.models.schemas import APIResponse, OptimizationRequest, OptimizationResult
from app.services.optimizer import run_optimization
from app.services.solar_forecast import SolarForecastService

router = APIRouter()

# Bounded in-process result store. Replace with Redis when horizontally scaling —
# this only protects a single worker from unbounded memory growth.
_RESULT_STORE_MAX_ENTRIES = 100
_RESULT_STORE_TTL = timedelta(hours=24)
optimization_results: "OrderedDict[str, dict]" = OrderedDict()
_results_lock = Lock()


def _evict_stale_results() -> None:
    """Drop expired entries and enforce capacity (LRU)."""
    now = datetime.now()
    with _results_lock:
        # TTL eviction
        expired = [
            jid
            for jid, v in optimization_results.items()
            if now - v["timestamp"] > _RESULT_STORE_TTL
        ]
        for jid in expired:
            optimization_results.pop(jid, None)
        # Capacity eviction (oldest first)
        while len(optimization_results) > _RESULT_STORE_MAX_ENTRIES:
            optimization_results.popitem(last=False)


def _store_result(
    job_id: str, request: OptimizationRequest, result: OptimizationResult
) -> None:
    with _results_lock:
        optimization_results[job_id] = {
            "request": request,
            "result": result,
            "timestamp": datetime.now(),
        }
        optimization_results.move_to_end(job_id)
    _evict_stale_results()


@router.post("/run", response_model=APIResponse)
async def run_optimization_endpoint(request: OptimizationRequest):
    """
    Run unit commitment and economic dispatch optimization

    Solves the MILP problem to minimize operational costs while meeting:
    - Load demand
    - Reserve requirements
    - Generator constraints
    - Solar PV integration
    - Battery storage optimization
    """
    try:
        logger.info(
            f"Starting optimization: {len(request.load_profile)} periods, {len(request.generators)} generators"
        )

        # Validate request
        if len(request.load_profile) < 2:
            raise HTTPException(
                status_code=400, detail="Load profile must have at least 2 time periods"
            )

        if len(request.generators) < 1:
            raise HTTPException(
                status_code=400, detail="At least one generator is required"
            )

        # Run optimization
        result = run_optimization(request)

        # Store result
        job_id = str(uuid.uuid4())
        _store_result(job_id, request, result)

        logger.info(
            f"Optimization completed: {result.status}, Cost: Rp {result.total_cost:,.0f}"
        )

        return APIResponse(
            success=True,
            data={
                "job_id": job_id,
                "result": result.model_dump(),
            },
            message=f"Optimization completed successfully. Total cost: Rp {result.total_cost:,.0f}",
        )

    except Exception as e:
        logger.error(f"Optimization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.get("/results/{job_id}", response_model=APIResponse)
async def get_optimization_results(job_id: str):
    """Retrieve optimization results by job ID"""

    _evict_stale_results()
    with _results_lock:
        stored = optimization_results.get(job_id)
        if stored is None:
            raise HTTPException(status_code=404, detail="Optimization job not found")
        # Touch for LRU
        optimization_results.move_to_end(job_id)

    return APIResponse(
        success=True,
        data=stored["result"],
        message=f"Results from {stored['timestamp'].isoformat()}",
    )


@router.post("/run-with-solar", response_model=APIResponse)
async def run_optimization_with_solar(request: OptimizationRequest):
    """
    Run optimization with automatic solar forecasting

    Automatically generates solar forecast based on:
    - Location (default: Bandung)
    - Weather data
    - PV system specifications
    """
    try:
        logger.info("Running optimization with solar forecasting")

        # Generate solar forecast if not provided
        if request.solar_forecast is None and request.pv_system_capacity:
            solar_service = SolarForecastService()

            # Determine forecast horizon from load profile
            horizon_hours = len(request.load_profile) * settings.TIME_RESOLUTION

            forecast = solar_service.generate_forecast(
                capacity=request.pv_system_capacity,
                horizon_hours=horizon_hours,
            )

            request.solar_forecast = forecast["generation"]
            logger.info(
                f"Generated solar forecast: {sum(forecast['generation']):.1f} kWh total"
            )

        # Run optimization
        result = run_optimization(request)

        job_id = str(uuid.uuid4())
        _store_result(job_id, request, result)

        return APIResponse(
            success=True,
            data={
                "job_id": job_id,
                "result": result.model_dump(),
            },
            message=f"Optimization with solar completed. Cost: Rp {result.total_cost:,.0f}",
        )

    except Exception as e:
        logger.error(f"Optimization with solar failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_solver_status():
    """Get solver configuration and availability"""

    return APIResponse(
        success=True,
        data={
            "solver": settings.SOLVER_NAME,
            "time_limit": settings.SOLVER_TIME_LIMIT,
            "optimization_horizon": settings.OPTIMIZATION_HORIZON,
            "time_resolution": settings.TIME_RESOLUTION,
            "location": {
                "latitude": settings.LATITUDE,
                "longitude": settings.LONGITUDE,
                "timezone": settings.TIMEZONE,
            },
        },
        message="Solver ready",
    )


@router.delete("/results/{job_id}")
async def delete_optimization_result(job_id: str):
    """Delete optimization results"""

    with _results_lock:
        if optimization_results.pop(job_id, None) is None:
            raise HTTPException(status_code=404, detail="Job not found")

    return APIResponse(
        success=True,
        message="Results deleted successfully",
    )


@router.get("/results")
async def list_optimization_results(limit: int = 10):
    """List recent optimization jobs"""

    _evict_stale_results()
    with _results_lock:
        jobs = sorted(
            optimization_results.items(),
            key=lambda x: x[1]["timestamp"],
            reverse=True,
        )[:limit]

    return APIResponse(
        success=True,
        data=[
            {
                "job_id": job_id,
                "timestamp": stored["timestamp"].isoformat(),
                "status": stored["result"].status,
                "total_cost": stored["result"].total_cost,
                "solve_time": stored["result"].solve_time,
            }
            for job_id, stored in jobs
        ],
        message=f"Showing {len(jobs)} recent jobs",
    )
