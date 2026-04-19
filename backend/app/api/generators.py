"""
Generators API endpoints - Manage generator fleet
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from loguru import logger

from app.models.schemas import GeneratorData, APIResponse
from app.core.config import settings

router = APIRouter()

# In-memory generator templates (use database in production)
generator_templates = {
    'diesel_small': {
        'name': 'Small Diesel Generator',
        'fuel_type': 'Diesel',
        'min_output': 5,
        'max_output': 50,
        'ramp_up': 25,
        'ramp_down': 25,
        'min_uptime': 1,
        'min_downtime': 1,
        'startup_cost': 100000,
        'shutdown_cost': 0,
        'no_load_cost': 25000,
        'fuel_cost': 1200,
        'emissions_rate': 0.7,
    },
    'diesel_medium': {
        'name': 'Medium Diesel Generator',
        'fuel_type': 'Diesel',
        'min_output': 50,
        'max_output': 200,
        'ramp_up': 50,
        'ramp_down': 50,
        'min_uptime': 2,
        'min_downtime': 2,
        'startup_cost': 300000,
        'shutdown_cost': 0,
        'no_load_cost': 75000,
        'fuel_cost': 1100,
        'emissions_rate': 0.65,
    },
    'gas_turbine': {
        'name': 'Gas Turbine',
        'fuel_type': 'Natural Gas',
        'min_output': 10,
        'max_output': 100,
        'ramp_up': 50,
        'ramp_down': 50,
        'min_uptime': 2,
        'min_downtime': 2,
        'startup_cost': 500000,
        'shutdown_cost': 0,
        'no_load_cost': 50000,
        'fuel_cost': 800,
        'emissions_rate': 0.45,
    },
    'coal_small': {
        'name': 'Small Coal Plant',
        'fuel_type': 'Coal',
        'min_output': 50,
        'max_output': 500,
        'ramp_up': 25,
        'ramp_down': 25,
        'min_uptime': 8,
        'min_downtime': 8,
        'startup_cost': 2000000,
        'shutdown_cost': 500000,
        'no_load_cost': 200000,
        'fuel_cost': 500,
        'emissions_rate': 0.9,
    },
    'biomass': {
        'name': 'Biomass Generator',
        'fuel_type': 'Biomass',
        'min_output': 20,
        'max_output': 150,
        'ramp_up': 30,
        'ramp_down': 30,
        'min_uptime': 4,
        'min_downtime': 4,
        'startup_cost': 400000,
        'shutdown_cost': 0,
        'no_load_cost': 60000,
        'fuel_cost': 600,
        'emissions_rate': 0.15,  # Carbon neutral-ish
    },
}


@router.get("/templates", response_model=APIResponse)
async def get_generator_templates():
    """Get available generator templates for Indonesian market"""
    
    templates = []
    for key, data in generator_templates.items():
        templates.append({
            'id': key,
            **data,
        })
    
    return APIResponse(
        success=True,
        data=templates,
        message=f"Available {len(templates)} generator templates",
    )


@router.get("/templates/{template_id}", response_model=APIResponse)
async def get_generator_template(template_id: str):
    """Get specific generator template"""
    
    if template_id not in generator_templates:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return APIResponse(
        success=True,
        data={
            'id': template_id,
            **generator_templates[template_id],
        },
        message=f"Template: {generator_templates[template_id]['name']}",
    )


@router.post("/create", response_model=APIResponse)
async def create_generator(generator: GeneratorData):
    """Create custom generator configuration"""
    
    # Validate generator data
    if generator.min_output > generator.max_output:
        raise HTTPException(
            status_code=400,
            detail="Minimum output cannot exceed maximum output",
        )
    
    if generator.ramp_up > generator.max_output:
        raise HTTPException(
            status_code=400,
            detail="Ramp up rate exceeds maximum output",
        )
    
    logger.info(f"Creating generator: {generator.name} ({generator.max_output}kW)")
    
    # In production, save to database
    # For now, just return the generator
    return APIResponse(
        success=True,
        data=generator.model_dump(),
        message=f"Generator '{generator.name}' created successfully",
    )


@router.get("/presets/indonesia", response_model=APIResponse)
async def get_indonesia_presets():
    """
    Get generator presets optimized for Indonesian market
    
    Includes typical PLN and IPP configurations with IDR pricing
    """
    
    presets = {
        'pln_small_island': {
            'name': 'Small Island System (PLN)',
            'description': 'Typical small island diesel + solar hybrid',
            'generators': [
                {**generator_templates['diesel_medium'], 'generator_id': 0},
                {**generator_templates['diesel_small'], 'generator_id': 1},
            ],
            'solar_capacity': 100,  # kW
            'battery_capacity': 200,  # kWh
        },
        'industrial_cogen': {
            'name': 'Industrial Cogeneration',
            'description': 'Factory with gas turbine and backup diesel',
            'generators': [
                {**generator_templates['gas_turbine'], 'generator_id': 0},
                {**generator_templates['diesel_medium'], 'generator_id': 1},
            ],
            'solar_capacity': 50,
            'battery_capacity': 100,
        },
        'commercial_rooftop': {
            'name': 'Commercial Building + Rooftop Solar',
            'description': 'Office building with solar and diesel backup',
            'generators': [
                {**generator_templates['diesel_small'], 'generator_id': 0},
            ],
            'solar_capacity': 200,
            'battery_capacity': 150,
        },
        'rural_microgrid': {
            'name': 'Rural Microgrid',
            'description': 'Village microgrid with diesel + solar + battery',
            'generators': [
                {**generator_templates['diesel_small'], 'generator_id': 0},
            ],
            'solar_capacity': 75,
            'battery_capacity': 300,
        },
    }
    
    return APIResponse(
        success=True,
        data=presets,
        message="Indonesian market presets loaded",
    )


@router.post("/validate", response_model=APIResponse)
async def validate_generator_fleet(generators: List[GeneratorData]):
    """
    Validate generator fleet configuration
    
    Checks for:
    - Sufficient capacity for typical loads
    - Reserve margin adequacy
    - Ramp rate compatibility
    """
    
    warnings = []
    errors = []
    
    if not generators:
        return APIResponse(
            success=False,
            error="No generators provided",
        )
    
    total_capacity = sum(g.max_output for g in generators)
    total_min = sum(g.min_output for g in generators)
    
    # Check capacity
    if total_capacity < 100:
        warnings.append("Total capacity is low (< 100 kW)")
    
    # Check reserve margin
    reserve_margin = (total_capacity - total_min) / total_capacity * 100 if total_capacity > 0 else 0
    if reserve_margin < 15:
        warnings.append(f"Reserve margin is low ({reserve_margin:.1f}%)")
    
    # Check for diversity
    fuel_types = set(g.fuel_type for g in generators)
    if len(fuel_types) == 1 and len(generators) > 2:
        warnings.append("All generators use the same fuel type - consider diversification")
    
    # Check ramp rates
    for gen in generators:
        if gen.ramp_up < gen.max_output / 10:
            warnings.append(f"{gen.name}: Ramp rate may be too slow")
    
    return APIResponse(
        success=True,
        data={
            'total_capacity': total_capacity,
            'total_min_output': total_min,
            'reserve_margin': reserve_margin,
            'fuel_diversity': len(fuel_types),
            'warnings': warnings,
            'errors': errors,
        },
        message="Validation complete" if not errors else "Validation completed with errors",
    )
