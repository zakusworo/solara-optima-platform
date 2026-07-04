"""
Carbon-credit & I-REC estimation for the rooftop-solar aggregation layer.

Turns solar generation (kWh) into:
- Issuable I-REC (International Renewable Energy Certificate) units — 1 cert per
  MWh of renewable generation, scaled by an eligibility/registration factor.
- Avoided grid CO2 (tonnes), using Indonesia's grid emission factor.
- Indicative credit revenue (IDR + USD), using a configurable I-REC unit price.

These are *indicative* figures for the CIIC carbon-credit framing, not a guarantee
of issuance or price. I-REC and avoided-CO2 credits are distinct instruments; to
avoid double-counting a project typically monetises one or the other — both are
shown for transparency.
"""

from typing import Optional

from app.core.config import settings

# Indonesia grid emission factor (JAMALI interconnection), kgCO2/kWh.
# Kept consistent with finance.GRID_EMISSION_FACTOR_KG_PER_KWH; callers may pass
# finance's value explicitly to guarantee a single source of truth.
EMISSION_FACTOR_KG_PER_KWH = 0.85

# I-REC: 1 certificate = 1 MWh. Not every generated MWh is registrable
# (metering/verification lag, partial-year availability) — apply an eligibility
# factor to stay conservative.
IREC_ELIGIBILITY_FACTOR = 0.95

_NOTE = (
    "Indicative. I-REC = 1 cert/MWh (x eligibility). Avoided CO2 uses the "
    "Indonesia grid emission factor. I-REC and carbon credits are separate "
    "instruments; avoid double-counting."
)


def estimate(
    annual_generation_kwh: float,
    irec_price_usd: Optional[float] = None,
    usd_idr: Optional[float] = None,
    emission_factor_kg_per_kwh: Optional[float] = None,
    eligibility_factor: Optional[float] = None,
) -> dict:
    """Indicative I-REC / avoided-CO2 / credit-revenue estimate for a year of solar."""
    irec_price = (
        irec_price_usd if irec_price_usd is not None else settings.IREC_PRICE_USD
    )
    fx = usd_idr if usd_idr is not None else settings.USD_IDR_RATE
    ef = (
        emission_factor_kg_per_kwh
        if emission_factor_kg_per_kwh is not None
        else EMISSION_FACTOR_KG_PER_KWH
    )
    elig = (
        eligibility_factor
        if eligibility_factor is not None
        else IREC_ELIGIBILITY_FACTOR
    )

    if not annual_generation_kwh or annual_generation_kwh <= 0:
        return {
            "annual_generation_mwh": 0.0,
            "irecs_issuable": 0.0,
            "irec_price_usd": irec_price,
            "avoided_co2_tonnes": 0.0,
            "emission_factor_kg_per_kwh": ef,
            "eligibility_factor": elig,
            "indicative_revenue_usd": 0.0,
            "indicative_revenue_idr": 0.0,
            "fx_usd_idr": fx,
            "note": _NOTE,
        }

    annual_mwh = annual_generation_kwh / 1000.0
    irecs = annual_mwh * elig
    avoided_tco2 = annual_generation_kwh * ef / 1000.0  # kg -> tonnes
    revenue_usd = irecs * irec_price
    revenue_idr = revenue_usd * fx
    return {
        "annual_generation_mwh": round(annual_mwh, 1),
        "irecs_issuable": round(irecs, 1),
        "irec_price_usd": irec_price,
        "avoided_co2_tonnes": round(avoided_tco2, 1),
        "emission_factor_kg_per_kwh": ef,
        "eligibility_factor": elig,
        "indicative_revenue_usd": round(revenue_usd, 2),
        "indicative_revenue_idr": round(revenue_idr),
        "fx_usd_idr": fx,
        "note": _NOTE,
    }
