"""
Optimization API endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from loguru import logger
import uuid
from datetime import datetime

from app.models.schemas import (
    OptimizationRequest,
    OptimizationResult,
    APIResponse,
)
from app.services.optimizer import run_optimization
from app.services.solar_forecast import SolarForecastService
from app.core.config import settings

router = APIRouter()

# Store optimization results temporarily (use Redis in production)
optimization_results = {}


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
        logger.info(f"Starting optimization: {len(request.load_profile)} periods, {len(request.generators)} generators")
        
        # Validate request
        if len(request.load_profile) < 2:
            raise HTTPException(status_code=400, detail="Load profile must have at least 2 time periods")
        
        if len(request.generators) < 1:
            raise HTTPException(status_code=400, detail="At least one generator is required")
        
        # Run optimization
        result = run_optimization(request)
        
        # Store result
        job_id = str(uuid.uuid4())
        optimization_results[job_id] = {
            "request": request,
            "result": result,
            "timestamp": datetime.now(),
        }
        
        logger.info(f"Optimization completed: {result.status}, Cost: Rp {result.total_cost:,.0f}")
        
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
    
    if job_id not in optimization_results:
        raise HTTPException(status_code=404, detail="Optimization job not found")
    
    stored = optimization_results[job_id]
    
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
            
            request.solar_forecast = forecast['generation']
            logger.info(f"Generated solar forecast: {sum(forecast['generation']):.1f} kWh total")
        
        # Run optimization
        result = run_optimization(request)
        
        job_id = str(uuid.uuid4())
        optimization_results[job_id] = {
            "request": request,
            "result": result,
            "timestamp": datetime.now(),
        }
        
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
    
    if job_id not in optimization_results:
        raise HTTPException(status_code=404, detail="Job not found")
    
    del optimization_results[job_id]
    
    return APIResponse(
        success=True,
        message="Results deleted successfully",
    )


@router.get("/results")
async def list_optimization_results(limit: int = 10):
    """List recent optimization jobs"""
    
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
