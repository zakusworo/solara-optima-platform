"""
Solar Aggregation & Financing Marketplace API.

Endpoints that turn the pvlib generation engine into a rooftop-solar
go-to-market layer:

- GET  /tariffs         -> PLN tariff groups for the sizing form
- POST /estimate        -> size a system + full financing/impact analysis
- GET  /installers      -> browse EPC/installer partners (filterable)
- GET  /financiers      -> browse financing products (filterable)
- POST /match           -> match a sized project to installers + financiers
- POST /quote-request   -> submit a customer lead
- GET  /portfolio       -> aggregated pipeline stats (the "aggregation" story)
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.core.config import settings
from app.models.marketplace_schemas import (
    MatchRequest,
    QuoteRequest,
    SolarEstimateRequest,
)
from app.models.schemas import APIResponse
from app.services import finance

router = APIRouter()

_DATA_DIR = settings.BASE_DIR / "data"
_TARIFFS_FILE = _DATA_DIR / "pln_tariffs.json"
_INSTALLERS_FILE = _DATA_DIR / "installers.json"
_FINANCIERS_FILE = _DATA_DIR / "financiers.json"
_LEADS_FILE = _DATA_DIR / "leads.jsonl"


def _load_json(path, key: str) -> List[Dict]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.error(f"Marketplace data file missing: {path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Marketplace data file is not valid JSON ({path}): {e}")
        return []
    return raw.get(key, [])


_tariffs: List[Dict] = _load_json(_TARIFFS_FILE, "tariffs")
_installers: List[Dict] = _load_json(_INSTALLERS_FILE, "installers")
_financiers: List[Dict] = _load_json(_FINANCIERS_FILE, "financiers")


def _find_tariff(code: str) -> Optional[Dict]:
    return next((t for t in _tariffs if t["code"] == code), None)


@router.get("/tariffs", response_model=APIResponse)
async def get_tariffs():
    """PLN tariff groups used to convert a bill into kWh."""
    return APIResponse(
        success=True,
        data=_tariffs,
        message=f"{len(_tariffs)} PLN tariff groups",
    )


@router.post("/estimate", response_model=APIResponse)
async def estimate(request: SolarEstimateRequest):
    """Size a rooftop system and run the full financing + CO2 analysis."""
    tariff = _find_tariff(request.tariff_code)
    if tariff is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown tariff_code '{request.tariff_code}'. See /api/v1/marketplace/tariffs.",
        )
    if not any(
        [request.monthly_bill_idr, request.monthly_consumption_kwh, request.desired_capacity_kwp]
    ):
        raise HTTPException(
            status_code=400,
            detail="Provide one of: monthly_bill_idr, monthly_consumption_kwh, or desired_capacity_kwp.",
        )

    result = finance.analyze(request, tariff_idr_per_kwh=tariff["price_idr_per_kwh"])
    logger.info(
        f"Estimate: {result.recommended_capacity_kwp} kWp, "
        f"payback={result.payback_years}y, score={result.bankability_score}"
    )
    return APIResponse(
        success=True,
        data=result,
        message="Solar estimate generated",
    )


def _filter_installers(
    capacity_kwp: float, segment: str, region: Optional[str]
) -> List[Dict]:
    matches = []
    for ins in _installers:
        if not (ins["min_kwp"] <= capacity_kwp <= ins["max_kwp"]):
            continue
        if segment not in ins.get("segments", []):
            continue
        regions = ins.get("regions", [])
        if region and "nationwide" not in regions and region not in regions:
            continue
        matches.append(ins)
    matches.sort(key=lambda i: i.get("rating", 0), reverse=True)
    return matches


def _filter_financiers(
    segment: str, capex_idr: Optional[float]
) -> List[Dict]:
    matches = []
    for fin in _financiers:
        if segment not in fin.get("segments", []):
            continue
        if capex_idr is not None:
            lo = fin.get("min_ticket_idr", 0)
            hi = fin.get("max_ticket_idr", float("inf"))
            if not (lo <= capex_idr <= hi):
                continue
        matches.append(fin)
    return matches


@router.get("/installers", response_model=APIResponse)
async def get_installers(
    capacity_kwp: Optional[float] = Query(None, gt=0),
    segment: Optional[str] = None,
    region: Optional[str] = None,
):
    """Browse installer partners, optionally filtered by project fit."""
    data = _installers
    if capacity_kwp is not None or segment is not None or region is not None:
        data = _filter_installers(
            capacity_kwp=capacity_kwp or 0.5,
            segment=segment or "commercial",
            region=region,
        )
    return APIResponse(success=True, data=data, message=f"{len(data)} installers")


@router.get("/financiers", response_model=APIResponse)
async def get_financiers(
    segment: Optional[str] = None,
    capex_idr: Optional[float] = Query(None, ge=0),
):
    """Browse financing products, optionally filtered by segment/ticket."""
    data = _financiers
    if segment is not None or capex_idr is not None:
        data = _filter_financiers(segment=segment or "commercial", capex_idr=capex_idr)
    return APIResponse(success=True, data=data, message=f"{len(data)} financiers")


@router.post("/match", response_model=APIResponse)
async def match(request: MatchRequest):
    """Match a sized project to the best-fit installers and financiers."""
    installers = _filter_installers(
        capacity_kwp=request.capacity_kwp,
        segment=request.segment.value,
        region=request.region,
    )[: request.limit]
    financiers = _filter_financiers(
        segment=request.segment.value, capex_idr=request.capex_idr
    )[: request.limit]
    return APIResponse(
        success=True,
        data={"installers": installers, "financiers": financiers},
        message=f"{len(installers)} installers, {len(financiers)} financiers matched",
    )


@router.post("/quote-request", response_model=APIResponse)
async def quote_request(request: QuoteRequest):
    """Submit a customer lead (persisted to data/leads.jsonl)."""
    lead = request.model_dump()
    lead["lead_id"] = f"lead-{uuid4().hex[:10]}"
    lead["created_at"] = datetime.now(timezone.utc).isoformat()
    if request.segment:
        lead["segment"] = request.segment.value
    if request.preferred_financing:
        lead["preferred_financing"] = request.preferred_financing.value
    try:
        with _LEADS_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(lead) + "\n")
    except OSError as e:  # pragma: no cover - non-fatal
        logger.error(f"Could not persist lead: {e}")
    logger.info(f"New quote request: {lead['lead_id']} ({request.email})")
    return APIResponse(
        success=True,
        data={"lead_id": lead["lead_id"]},
        message="Quote request received. A partner will be in touch.",
    )


@router.get("/portfolio", response_model=APIResponse)
async def portfolio():
    """
    Aggregated pipeline stats across submitted leads — the 'aggregation' view
    that turns many small rooftops into one investable portfolio.
    """
    total_leads = 0
    total_capacity = 0.0
    total_capex = 0.0
    total_bill = 0.0
    if _LEADS_FILE.exists():
        for line in _LEADS_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                lead = json.loads(line)
            except json.JSONDecodeError:
                continue
            total_leads += 1
            total_capacity += lead.get("capacity_kwp") or 0.0
            total_bill += lead.get("monthly_bill_idr") or 0.0

    # Approximate portfolio economics from aggregated capacity
    if total_capacity > 0:
        total_capex = total_capacity * finance.capex_per_kwp(total_capacity)
    annual_gen = total_capacity * finance.DEFAULT_SPECIFIC_YIELD
    annual_co2_t = annual_gen * finance.GRID_EMISSION_FACTOR_KG_PER_KWH / 1000.0

    return APIResponse(
        success=True,
        data={
            "total_leads": total_leads,
            "total_capacity_kwp": round(total_capacity, 1),
            "estimated_total_capex_idr": round(total_capex),
            "aggregated_monthly_bill_idr": round(total_bill),
            "portfolio_annual_generation_kwh": round(annual_gen),
            "portfolio_annual_co2_avoided_tonnes": round(annual_co2_t, 1),
        },
        message="Portfolio aggregation",
    )
