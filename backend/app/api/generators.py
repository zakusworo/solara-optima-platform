"""
Generators API endpoints - Manage generator fleet
"""

import json
from typing import Dict, List

from fastapi import APIRouter, HTTPException
from loguru import logger

from app.core.config import settings
from app.models.schemas import APIResponse, GeneratorData

router = APIRouter()

# Generator templates and Indonesia-market presets are defined in
# backend/data/generator_templates.json so non-developers can edit them
# without touching code. Loaded once at import.
_TEMPLATES_FILE = settings.BASE_DIR / "data" / "generator_templates.json"


def _load_template_data() -> Dict[str, Dict]:
    try:
        raw = json.loads(_TEMPLATES_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.error(f"Generator templates file missing: {_TEMPLATES_FILE}")
        return {"templates": {}, "presets": {}}
    except json.JSONDecodeError as e:
        logger.error(f"Generator templates file is not valid JSON: {e}")
        return {"templates": {}, "presets": {}}
    return {
        "templates": raw.get("templates", {}),
        "presets": raw.get("presets", {}),
    }


_data = _load_template_data()
generator_templates: Dict[str, Dict] = _data["templates"]
_presets_raw: Dict[str, Dict] = _data["presets"]


def _expand_preset(preset: Dict) -> Dict:
    """Inline generator templates referenced by ID into the preset response."""
    template_ids = preset.get("generator_template_ids", [])
    expanded_generators = []
    for idx, template_id in enumerate(template_ids):
        if template_id not in generator_templates:
            logger.warning(
                f"Preset references unknown generator template '{template_id}'"
            )
            continue
        expanded_generators.append(
            {**generator_templates[template_id], "generator_id": idx}
        )
    return {
        "name": preset.get("name"),
        "description": preset.get("description"),
        "generators": expanded_generators,
        "solar_capacity": preset.get("solar_capacity"),
        "battery_capacity": preset.get("battery_capacity"),
    }


@router.get("/templates", response_model=APIResponse)
async def get_generator_templates():
    """Get available generator templates for Indonesian market"""

    templates = [{"id": key, **data} for key, data in generator_templates.items()]

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
            "id": template_id,
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

    Includes typical PLN and IPP configurations with IDR pricing.
    Edit backend/data/generator_templates.json to add or modify presets.
    """

    presets = {key: _expand_preset(preset) for key, preset in _presets_raw.items()}

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
    reserve_margin = (
        (total_capacity - total_min) / total_capacity * 100 if total_capacity > 0 else 0
    )
    if reserve_margin < 15:
        warnings.append(f"Reserve margin is low ({reserve_margin:.1f}%)")

    # Check for diversity
    fuel_types = set(g.fuel_type for g in generators)
    if len(fuel_types) == 1 and len(generators) > 2:
        warnings.append(
            "All generators use the same fuel type - consider diversification"
        )

    # Check ramp rates
    for gen in generators:
        if gen.ramp_up < gen.max_output / 10:
            warnings.append(f"{gen.name}: Ramp rate may be too slow")

    return APIResponse(
        success=True,
        data={
            "total_capacity": total_capacity,
            "total_min_output": total_min,
            "reserve_margin": reserve_margin,
            "fuel_diversity": len(fuel_types),
            "warnings": warnings,
            "errors": errors,
        },
        message=(
            "Validation complete" if not errors else "Validation completed with errors"
        ),
    )
