"""
Solar techno-economic & financing engine.

Turns the pvlib generation model into a *bankable* proposition for a rooftop
customer: system sizing from a PLN bill, self-consumption-aware savings, CAPEX,
CO2 avoided, and side-by-side cash / loan / PPA economics (payback, IRR, NPV).

All assumptions below are illustrative defaults for the Indonesian market and
are surfaced in the API response so they can be reviewed and overridden. They
are NOT a financial guarantee.
"""

from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger

from app.core.config import settings
from app.models.marketplace_schemas import (
    FinancingOption,
    FinancingType,
    SolarEstimateRequest,
    SolarEstimateResult,
)
from app.services.solar_forecast import SolarForecastService
from app.services import carbon_credits as cc

# --- Techno-economic assumptions (Indonesia, illustrative; override via request) ---
SYSTEM_LIFETIME_YEARS = 25
PANEL_DEGRADATION_PER_YEAR = 0.005          # 0.5%/yr output loss
OM_COST_PCT_OF_CAPEX = 0.01                 # 1%/yr operations & maintenance
TARIFF_ESCALATION_PER_YEAR = 0.03           # PLN tariff drift
DISCOUNT_RATE = 0.10                        # NPV discount rate
GRID_EMISSION_FACTOR_KG_PER_KWH = 0.85      # Indonesia grid (JAMALI interconnection)
CLEARSKY_TO_REAL_DERATE = 0.72              # clear-sky annual -> weather-adjusted
DEFAULT_SPECIFIC_YIELD = 1450.0             # kWh/kWp/yr fallback
PANEL_WATT = 550                            # W per module (panel-count estimate)
AREA_PER_KWP_M2 = 7.0                       # rooftop area per kWp
CO2_PER_TREE_KG_PER_YEAR = 21.0            # sequestration equivalent
EXPORT_PRICE_IDR_PER_KWH = 0.0              # PLN export credit removed (Permen ESDM 2/2024)

# Self-consumption ratio & default bill-offset target by segment
SELF_CONSUMPTION_BY_SEGMENT = {
    "residential": 0.55,
    "commercial": 0.75,
    "industrial": 0.85,
}
DEFAULT_TARGET_OFFSET_BY_SEGMENT = {
    "residential": 0.50,
    "commercial": 0.80,
    "industrial": 1.00,
}

# Financing defaults
DEFAULT_LOAN_INTEREST = 0.115
DEFAULT_LOAN_TENOR_MONTHS = 84
DEFAULT_DOWN_PAYMENT_PCT = 0.10
PPA_DISCOUNT_VS_TARIFF = 0.15               # PPA price this fraction below grid tariff
PPA_ESCALATION_PER_YEAR = 0.02
PPA_TERM_YEARS = 20


# --------------------------------------------------------------------------- #
# Financial primitives
# --------------------------------------------------------------------------- #
def npv(rate: float, cashflows: List[float]) -> float:
    """Net present value; cashflows[0] is year 0."""
    return sum(cf / (1.0 + rate) ** i for i, cf in enumerate(cashflows))


def irr(cashflows: List[float]) -> Optional[float]:
    """Internal rate of return via bisection. Returns None if no sign change."""
    low, high = -0.9, 1.0
    f_low, f_high = npv(low, cashflows), npv(high, cashflows)
    if f_low * f_high > 0:
        return None
    for _ in range(200):
        mid = (low + high) / 2.0
        f_mid = npv(mid, cashflows)
        if abs(f_mid) < 1.0:  # within Rp1 — plenty precise for IDR
            return mid
        if f_low * f_mid < 0:
            high, f_high = mid, f_mid
        else:
            low, f_low = mid, f_mid
    return (low + high) / 2.0


def annuity_payment(principal: float, annual_rate: float, months: int) -> float:
    """Fixed monthly loan payment (amortizing)."""
    if months <= 0 or principal <= 0:
        return 0.0
    r = annual_rate / 12.0
    if r == 0:
        return principal / months
    return principal * r / (1.0 - (1.0 + r) ** (-months))


def payback_from_cumulative(cum: List[float]) -> Optional[float]:
    """First year the cumulative cashflow turns non-negative (interpolated)."""
    for i in range(1, len(cum)):
        if cum[i] >= 0:
            prev = cum[i - 1]
            span = cum[i] - prev
            frac = (-prev / span) if span != 0 else 0.0
            return round((i - 1) + frac, 1)
    return None


def capex_per_kwp(capacity_kwp: float) -> float:
    """Installed cost per kWp — declining with scale (Rp/kWp)."""
    if capacity_kwp < 10:
        return 15_000_000
    if capacity_kwp < 100:
        return 13_000_000
    if capacity_kwp < 1000:
        return 11_500_000
    return 10_000_000


# --------------------------------------------------------------------------- #
# Generation
# --------------------------------------------------------------------------- #
def estimate_specific_yield(
    latitude: Optional[float] = None, longitude: Optional[float] = None
) -> tuple:
    """Annual kWh per kWp and the irradiance source used.

    Returns (yield_kwh_per_kwp, source_str). When an explicit site lat/lon is
    supplied and PVGIS is available, the yield comes from a full-year run over a
    real satellite TMY (cloud-adjusted, no derate needed). Otherwise it falls
    back to a clear-sky equinox day x 365 with a weather derate. The source
    string is surfaced to the user so the estimate's basis is transparent.
    """
    # Real-irradiance path: only when a specific site location was provided.
    if latitude is not None and longitude is not None and settings.ENABLE_PVGIS:
        try:
            service = SolarForecastService(latitude=latitude, longitude=longitude)
            # start/end are ignored on the PVGIS branch (full TMY year) but are
            # used if PVGIS is unavailable and get_weather_data drops to clear-sky.
            forecast = service.generate_forecast(
                capacity=1.0,
                weather_source="pvgis",
                start=datetime(2024, 3, 21, 0, 0),
                end=datetime(2024, 3, 21, 23, 0),
            )
            # PVGIS branch returns a full 8760-h TMY; a clear-sky fallback
            # returns ~24 h for the equinox day — distinguish by row count.
            if len(forecast["timestamps"]) > 100 and forecast["total_generation"] > 0:
                return round(forecast["total_generation"], 1), "PVGIS satellite TMY (real irradiance)"
            # PVGIS unavailable -> generate_forecast already fell back to a
            # clear-sky equinox day; annualize it with the weather derate.
            annual = forecast["total_generation"] * 365 * CLEARSKY_TO_REAL_DERATE
            if annual > 0:
                return round(annual, 1), "clear-sky model (PVGIS offline)"
        except Exception as e:  # pragma: no cover - defensive fallback
            logger.warning(f"PVGIS yield calc failed ({e}); using clear-sky")

    # Fallback: clear-sky equinox day x 365, weather-derated.
    try:
        service = SolarForecastService(latitude=latitude, longitude=longitude)
        forecast = service.generate_forecast(
            capacity=1.0,
            start=datetime(2024, 3, 21, 0, 0),  # equinox: representative day
            end=datetime(2024, 3, 21, 23, 0),
        )
        daily_kwh_per_kwp = forecast["total_generation"]
        annual = daily_kwh_per_kwp * 365 * CLEARSKY_TO_REAL_DERATE
        if annual <= 0:
            return DEFAULT_SPECIFIC_YIELD, "default (clear-sky unavailable)"
        return round(annual, 1), "clear-sky model (no site coordinates)"
    except Exception as e:  # pragma: no cover - defensive fallback
        logger.warning(f"Specific-yield calc failed ({e}); using default")
        return DEFAULT_SPECIFIC_YIELD, "default fallback"


# --------------------------------------------------------------------------- #
# Main analysis
# --------------------------------------------------------------------------- #
def analyze(request: SolarEstimateRequest, tariff_idr_per_kwh: float) -> SolarEstimateResult:
    """Size the system and run the full financing + impact analysis."""

    segment = request.segment.value
    self_cons = SELF_CONSUMPTION_BY_SEGMENT.get(segment, 0.75)
    target_offset = request.target_offset or DEFAULT_TARGET_OFFSET_BY_SEGMENT.get(
        segment, 0.8
    )
    tariff = tariff_idr_per_kwh

    # 1. Annual consumption (if the customer gave us bill or kWh)
    if request.monthly_consumption_kwh:
        monthly_kwh = request.monthly_consumption_kwh
    elif request.monthly_bill_idr:
        monthly_kwh = request.monthly_bill_idr / tariff
    else:
        monthly_kwh = None
    annual_consumption = monthly_kwh * 12 if monthly_kwh else None

    # 2. Specific yield from pvlib (real PVGIS TMY when site coords are given)
    specific_yield, weather_source = estimate_specific_yield(
        request.latitude, request.longitude
    )

    # 3. Capacity sizing (priority: explicit > consumption-driven > fallback)
    if request.desired_capacity_kwp:
        capacity = request.desired_capacity_kwp
    elif annual_consumption:
        capacity = (annual_consumption * target_offset) / specific_yield
    else:
        capacity = settings.PV_SYSTEM_CAPACITY

    # Roof-area cap
    roof_limited = False
    roof_required = capacity * AREA_PER_KWP_M2
    if request.roof_area_m2 and roof_required > request.roof_area_m2:
        capacity = request.roof_area_m2 / AREA_PER_KWP_M2
        roof_limited = True
    capacity = round(max(capacity, 0.5), 1)
    roof_required = round(capacity * AREA_PER_KWP_M2, 1)

    # 4. Generation & self-consumption (year 1)
    annual_generation = capacity * specific_yield
    if annual_consumption:
        self_consumed = min(annual_generation * self_cons, annual_consumption)
    else:
        self_consumed = annual_generation * self_cons
    exported = max(annual_generation - self_consumed, 0.0)

    # 5. CAPEX & O&M
    c_per_kwp = capex_per_kwp(capacity)
    capex = capacity * c_per_kwp
    om_cost = capex * OM_COST_PCT_OF_CAPEX

    # 6. Lifetime cashflow (cash purchase) with degradation + tariff escalation
    cashflows = [-capex]
    cum = [-capex]
    disc_gen = 0.0
    disc_cost = capex
    for year in range(1, SYSTEM_LIFETIME_YEARS + 1):
        deg = (1 - PANEL_DEGRADATION_PER_YEAR) ** (year - 1)
        tariff_y = tariff * (1 + TARIFF_ESCALATION_PER_YEAR) ** (year - 1)
        gen_y = annual_generation * deg
        if annual_consumption:
            self_y = min(gen_y * self_cons, annual_consumption)
        else:
            self_y = gen_y * self_cons
        exp_y = max(gen_y - self_y, 0.0)
        saving_y = self_y * tariff_y + exp_y * EXPORT_PRICE_IDR_PER_KWH - om_cost
        cashflows.append(saving_y)
        cum.append(cum[-1] + saving_y)
        disc_gen += gen_y / (1 + DISCOUNT_RATE) ** year
        disc_cost += om_cost / (1 + DISCOUNT_RATE) ** year

    annual_bill_saving = self_consumed * tariff + exported * EXPORT_PRICE_IDR_PER_KWH
    lcoe = disc_cost / disc_gen if disc_gen > 0 else 0.0

    payback = payback_from_cumulative(cum)
    project_irr = irr(cashflows)
    project_npv = npv(DISCOUNT_RATE, cashflows)
    lifetime_net = cum[-1]

    # 7. CO2 impact (all solar generation displaces grid)
    annual_co2_t = annual_generation * GRID_EMISSION_FACTOR_KG_PER_KWH / 1000.0
    lifetime_gen = sum(
        annual_generation * (1 - PANEL_DEGRADATION_PER_YEAR) ** (y - 1)
        for y in range(1, SYSTEM_LIFETIME_YEARS + 1)
    )
    lifetime_co2_t = lifetime_gen * GRID_EMISSION_FACTOR_KG_PER_KWH / 1000.0
    trees = int(annual_co2_t * 1000 / CO2_PER_TREE_KG_PER_YEAR)

    # 7b. Carbon-credit / I-REC potential (indicative)
    cc_block = cc.estimate(
        annual_generation,
        emission_factor_kg_per_kwh=GRID_EMISSION_FACTOR_KG_PER_KWH,
    )

    # 8. Financing menu
    financing_options = _build_financing_options(
        request=request,
        capex=capex,
        om_cost=om_cost,
        annual_generation=annual_generation,
        self_cons=self_cons,
        annual_consumption=annual_consumption,
        tariff=tariff,
        cash_cashflows=cashflows,
        cash_payback=payback,
        cash_irr=project_irr,
        cash_npv=project_npv,
        cash_lifetime=lifetime_net,
    )

    # 9. Bankability score (heuristic 0-100)
    score = _bankability_score(payback, project_irr, segment)

    assumptions = {
        "system_lifetime_years": SYSTEM_LIFETIME_YEARS,
        "specific_yield_kwh_per_kwp": specific_yield,
        "weather_source": weather_source,
        "capex_per_kwp_idr": c_per_kwp,
        "self_consumption_ratio": self_cons,
        "target_offset": target_offset,
        "grid_tariff_idr_per_kwh": tariff,
        "tariff_escalation_per_year": TARIFF_ESCALATION_PER_YEAR,
        "grid_emission_factor_kg_per_kwh": GRID_EMISSION_FACTOR_KG_PER_KWH,
        "panel_degradation_per_year": PANEL_DEGRADATION_PER_YEAR,
        "om_pct_of_capex": OM_COST_PCT_OF_CAPEX,
        "discount_rate": DISCOUNT_RATE,
        "export_price_idr_per_kwh": EXPORT_PRICE_IDR_PER_KWH,
        "disclaimer": "Illustrative estimate, not a financial guarantee. Assumptions are editable.",
    }

    return SolarEstimateResult(
        recommended_capacity_kwp=capacity,
        num_panels_estimate=int(round(capacity * 1000 / PANEL_WATT)),
        roof_area_required_m2=roof_required,
        roof_limited=roof_limited,
        specific_yield_kwh_per_kwp=specific_yield,
        annual_generation_kwh=round(annual_generation, 1),
        annual_self_consumed_kwh=round(self_consumed, 1),
        annual_exported_kwh=round(exported, 1),
        self_consumption_ratio=self_cons,
        capex_idr=round(capex),
        capex_per_kwp_idr=c_per_kwp,
        annual_bill_saving_idr=round(annual_bill_saving),
        annual_om_cost_idr=round(om_cost),
        grid_tariff_idr_per_kwh=tariff,
        lcoe_idr_per_kwh=round(lcoe, 1),
        payback_years=payback,
        irr_pct=round(project_irr * 100, 1) if project_irr is not None else None,
        npv_idr=round(project_npv),
        lifetime_net_saving_idr=round(lifetime_net),
        bankability_score=score,
        annual_co2_avoided_tonnes=round(annual_co2_t, 1),
        lifetime_co2_avoided_tonnes=round(lifetime_co2_t, 1),
        trees_equivalent_per_year=trees,
        carbon_credits=cc_block,
        financing_options=financing_options,
        cashflow_years=list(range(0, SYSTEM_LIFETIME_YEARS + 1)),
        cumulative_cashflow_cash_idr=[round(c) for c in cum],
        assumptions=assumptions,
    )


def _build_financing_options(
    *,
    request: SolarEstimateRequest,
    capex: float,
    om_cost: float,
    annual_generation: float,
    self_cons: float,
    annual_consumption: Optional[float],
    tariff: float,
    cash_cashflows: List[float],
    cash_payback: Optional[float],
    cash_irr: Optional[float],
    cash_npv: float,
    cash_lifetime: float,
) -> List[FinancingOption]:
    options: List[FinancingOption] = []

    # --- Cash purchase ---
    options.append(
        FinancingOption(
            type=FinancingType.cash,
            label="Cash Purchase",
            upfront_cost_idr=round(capex),
            monthly_payment_idr=0,
            tenor_months=0,
            year1_net_saving_idr=round(cash_cashflows[1]),
            lifetime_net_saving_idr=round(cash_lifetime),
            payback_years=cash_payback,
            irr_pct=round(cash_irr * 100, 1) if cash_irr is not None else None,
            npv_idr=round(cash_npv),
            description="Own the system outright; highest lifetime savings.",
        )
    )

    # --- Bank loan (amortizing) ---
    rate = request.loan_interest_rate if request.loan_interest_rate is not None else DEFAULT_LOAN_INTEREST
    tenor = request.loan_tenor_months or DEFAULT_LOAN_TENOR_MONTHS
    down_pct = request.down_payment_pct if request.down_payment_pct is not None else DEFAULT_DOWN_PAYMENT_PCT
    down = capex * down_pct
    principal = capex - down
    monthly = annuity_payment(principal, rate, tenor)
    annual_debt = monthly * 12
    tenor_years = tenor / 12.0

    loan_cf = [-down]
    loan_cum = [-down]
    for year in range(1, SYSTEM_LIFETIME_YEARS + 1):
        # reuse cash savings profile (already net of O&M)
        saving_y = cash_cashflows[year]
        debt = annual_debt if year <= tenor_years else 0.0
        net_y = saving_y - debt
        loan_cf.append(net_y)
        loan_cum.append(loan_cum[-1] + net_y)
    options.append(
        FinancingOption(
            type=FinancingType.loan,
            label="Green Term Loan",
            upfront_cost_idr=round(down),
            monthly_payment_idr=round(monthly),
            tenor_months=tenor,
            year1_net_saving_idr=round(loan_cf[1]),
            lifetime_net_saving_idr=round(loan_cum[-1]),
            payback_years=payback_from_cumulative(loan_cum),
            irr_pct=(lambda v: round(v * 100, 1) if v is not None else None)(irr(loan_cf)),
            npv_idr=round(npv(DISCOUNT_RATE, loan_cf)),
            description=f"{int(down_pct*100)}% down, {rate*100:.1f}%/yr, {int(tenor)}-month tenor. Savings can service the loan.",
        )
    )

    # --- PPA (zero CapEx) ---
    ppa_cf = [0.0]
    ppa_cum = [0.0]
    ppa_monthly_y1 = 0.0
    for year in range(1, SYSTEM_LIFETIME_YEARS + 1):
        within_term = year <= PPA_TERM_YEARS
        deg = (1 - PANEL_DEGRADATION_PER_YEAR) ** (year - 1)
        gen_y = annual_generation * deg
        if annual_consumption:
            self_y = min(gen_y * self_cons, annual_consumption)
        else:
            self_y = gen_y * self_cons
        tariff_y = tariff * (1 + TARIFF_ESCALATION_PER_YEAR) ** (year - 1)
        ppa_rate_y = (
            tariff * (1 - PPA_DISCOUNT_VS_TARIFF) * (1 + PPA_ESCALATION_PER_YEAR) ** (year - 1)
        )
        if within_term:
            customer_saving = self_y * (tariff_y - ppa_rate_y)
            if year == 1:
                ppa_monthly_y1 = self_y * ppa_rate_y / 12.0
        else:
            # After PPA term the customer typically owns the asset; approximate
            # with full grid-offset savings net of O&M.
            customer_saving = self_y * tariff_y - om_cost
        ppa_cf.append(customer_saving)
        ppa_cum.append(ppa_cum[-1] + customer_saving)
    options.append(
        FinancingOption(
            type=FinancingType.ppa,
            label="Zero-CapEx PPA",
            upfront_cost_idr=0,
            monthly_payment_idr=round(ppa_monthly_y1),
            tenor_months=PPA_TERM_YEARS * 12,
            year1_net_saving_idr=round(ppa_cf[1]),
            lifetime_net_saving_idr=round(ppa_cum[-1]),
            payback_years=0.0,  # no upfront cost -> immediate positive
            irr_pct=None,       # undefined without an initial outflow
            npv_idr=round(npv(DISCOUNT_RATE, ppa_cf)),
            description=f"No upfront cost. Buy solar kWh {int(PPA_DISCOUNT_VS_TARIFF*100)}% below PLN tariff for {PPA_TERM_YEARS} years.",
        )
    )

    return options


def _bankability_score(
    payback: Optional[float], project_irr: Optional[float], segment: str
) -> int:
    score = 50
    if payback is not None:
        if payback < 5:
            score += 25
        elif payback < 7:
            score += 15
        elif payback < 10:
            score += 5
        else:
            score -= 5
    if project_irr is not None:
        if project_irr > 0.18:
            score += 20
        elif project_irr > 0.12:
            score += 12
        elif project_irr > 0.08:
            score += 5
    if segment in ("commercial", "industrial"):
        score += 5  # stronger off-taker creditworthiness
    return max(0, min(100, score))
