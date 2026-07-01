"""
Pydantic schemas for the Solar Aggregation & Financing Marketplace.

These power the rooftop-solar advisory / financing layer that sits on top of
the pvlib generation engine: given a customer's bill or target capacity, the
platform sizes a system, computes bankable savings/ROI, quantifies CO2 avoided,
and matches the project to installers and financing products.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CustomerSegment(str, Enum):
    """Off-taker segment — drives self-consumption and default sizing."""

    residential = "residential"
    commercial = "commercial"  # SME / business
    industrial = "industrial"


class FinancingType(str, Enum):
    """Supported financing structures."""

    cash = "cash"
    loan = "loan"
    ppa = "ppa"
    lease = "lease"


class SolarEstimateRequest(BaseModel):
    """Input for a rooftop-solar sizing + financing estimate."""

    # Provide ONE of the following to drive sizing (priority: capacity > kWh > bill)
    monthly_bill_idr: Optional[float] = Field(
        None, ge=0, description="Average monthly electricity bill (IDR)"
    )
    monthly_consumption_kwh: Optional[float] = Field(
        None, ge=0, description="Average monthly consumption (kWh)"
    )
    desired_capacity_kwp: Optional[float] = Field(
        None, ge=0, description="Explicit target system size (kWp)"
    )

    tariff_code: str = Field(
        "B-2/TR-6600-200k", description="PLN tariff group code (see /marketplace/tariffs)"
    )
    segment: CustomerSegment = CustomerSegment.commercial
    roof_area_m2: Optional[float] = Field(
        None, ge=0, description="Usable roof area (m2) — caps recommended capacity"
    )
    target_offset: Optional[float] = Field(
        None,
        gt=0,
        le=1.5,
        description="Fraction of annual consumption to offset with solar generation",
    )

    # Location (defaults to backend config / Bandung)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Optional financing overrides
    loan_interest_rate: Optional[float] = Field(None, ge=0, le=1)
    loan_tenor_months: Optional[int] = Field(None, ge=1, le=360)
    down_payment_pct: Optional[float] = Field(None, ge=0, le=1)

    class Config:
        json_schema_extra = {
            "example": {
                "monthly_bill_idr": 25000000,
                "tariff_code": "B-2/TR-6600-200k",
                "segment": "commercial",
                "roof_area_m2": 800,
            }
        }


class FinancingOption(BaseModel):
    """A single financing structure with its economics for this project."""

    type: FinancingType
    label: str
    upfront_cost_idr: float
    monthly_payment_idr: float
    tenor_months: int
    year1_net_saving_idr: float
    lifetime_net_saving_idr: float
    payback_years: Optional[float]
    irr_pct: Optional[float]
    npv_idr: float
    description: str


class SolarEstimateResult(BaseModel):
    """Full sizing + financing + impact result for one site."""

    # Sizing & generation
    recommended_capacity_kwp: float
    num_panels_estimate: int
    roof_area_required_m2: float
    roof_limited: bool
    specific_yield_kwh_per_kwp: float
    annual_generation_kwh: float
    annual_self_consumed_kwh: float
    annual_exported_kwh: float
    self_consumption_ratio: float

    # Economics (headline: cash purchase)
    capex_idr: float
    capex_per_kwp_idr: float
    annual_bill_saving_idr: float
    annual_om_cost_idr: float
    grid_tariff_idr_per_kwh: float
    lcoe_idr_per_kwh: float
    payback_years: Optional[float]
    irr_pct: Optional[float]
    npv_idr: float
    lifetime_net_saving_idr: float
    bankability_score: int

    # Climate impact
    annual_co2_avoided_tonnes: float
    lifetime_co2_avoided_tonnes: float
    trees_equivalent_per_year: int

    # Financing menu + cashflow curve (cash purchase)
    financing_options: List[FinancingOption]
    cashflow_years: List[int]
    cumulative_cashflow_cash_idr: List[float]

    assumptions: Dict[str, Any]


class MatchRequest(BaseModel):
    """Request to match a sized project to installers + financiers."""

    capacity_kwp: float = Field(..., gt=0)
    capex_idr: Optional[float] = Field(None, ge=0)
    segment: CustomerSegment = CustomerSegment.commercial
    region: Optional[str] = Field(None, description="Province name, or omit for nationwide")
    limit: int = Field(5, ge=1, le=20)


class QuoteRequest(BaseModel):
    """A lead submitted by a prospective customer."""

    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    segment: CustomerSegment = CustomerSegment.commercial
    region: Optional[str] = None
    capacity_kwp: Optional[float] = Field(None, ge=0)
    monthly_bill_idr: Optional[float] = Field(None, ge=0)
    preferred_financing: Optional[FinancingType] = None
    installer_id: Optional[str] = None
    financier_id: Optional[str] = None
    notes: Optional[str] = None
