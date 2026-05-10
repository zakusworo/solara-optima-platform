"""
PV Module API endpoints - browse and select PV modules from CEC database
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from loguru import logger

from app.services.pv_module_db import get_pv_module_db

router = APIRouter()


@router.get("/modules/manufacturers")
async def get_manufacturers():
    """Get list of PV module manufacturers"""
    db = get_pv_module_db()
    return {"manufacturers": db.get_manufacturers()}


@router.get("/modules/technologies")
async def get_technologies():
    """Get list of PV module technologies"""
    db = get_pv_module_db()
    return {"technologies": db.get_technologies()}


@router.get("/modules/search")
async def search_modules(
    q: Optional[str] = Query(None, description="Search query string"),
    manufacturer: Optional[str] = Query(None, description="Filter by manufacturer"),
    technology: Optional[str] = Query(None, description="Filter by cell technology"),
    pmin: Optional[float] = Query(None, ge=0, description="Minimum power (W STC)"),
    pmax: Optional[float] = Query(None, ge=0, description="Maximum power (W STC)"),
    limit: int = Query(default=50, ge=1, le=500, description="Max results"),
):
    """
    Search CEC PV module database

    Returns matching PV modules with key parameters:
    - name, manufacturer, technology
    - p_stc (STC rated power in W)
    - p_ptc (PTC rated power in W)
    - efficiency
    - area, cells_in_series
    """
    try:
        db = get_pv_module_db()
        results = db.search_modules(
            query=q,
            manufacturer=manufacturer,
            technology=technology,
            pmin=pmin,
            pmax=pmax,
            limit=limit,
        )
        return {
            "count": len(results),
            "modules": results,
        }
    except Exception as e:
        logger.error(f"PV module search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/modules/{module_name}")
async def get_module_detail(module_name: str):
    """Get detailed parameters for a specific PV module"""
    db = get_pv_module_db()
    module = db.get_module(module_name)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return {"module": module}


@router.get("/modules/names")
async def get_module_names(
    limit: int = Query(default=1000, ge=1, le=5000),
):
    """Get a flat list of module names for autocomplete"""
    db = get_pv_module_db()
    return {"names": db.get_module_names(limit=limit)}
