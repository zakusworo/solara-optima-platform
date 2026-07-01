#!/usr/bin/env python3
"""Smoke test for the Solar Aggregation & Financing Marketplace layer."""

import sys

print("=" * 60)
print("Solara Optima - Marketplace Test Suite")
print("=" * 60)
print()

try:
    from app.services import finance
    from app.models.marketplace_schemas import SolarEstimateRequest, CustomerSegment
    print("✓ Marketplace modules import")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# --- Financial primitives sanity checks ---
assert abs(finance.npv(0.0, [-100, 50, 50, 50]) - 50) < 1e-6, "npv failed"
r = finance.irr([-100, 60, 60])
assert r is not None and 0.1 < r < 0.15, f"irr out of range: {r}"
pmt = finance.annuity_payment(100_000_000, 0.115, 84)
assert 1_500_000 < pmt < 2_000_000, f"annuity out of range: {pmt}"
print(f"✓ Financial primitives OK (irr={r:.3f}, monthly_pmt=Rp{pmt:,.0f})")
print()

# --- End-to-end estimate for an SME on a Rp25M/month bill ---
req = SolarEstimateRequest(
    monthly_bill_idr=25_000_000,
    tariff_code="B-2/TR-6600-200k",
    segment=CustomerSegment.commercial,
    roof_area_m2=800,
)
res = finance.analyze(req, tariff_idr_per_kwh=1444.70)

print("SME estimate (Rp25M/month bill, 800 m² roof):")
print(f"  Recommended size    : {res.recommended_capacity_kwp} kWp ({res.num_panels_estimate} panels)")
print(f"  Roof-limited        : {res.roof_limited}")
print(f"  Specific yield      : {res.specific_yield_kwh_per_kwp} kWh/kWp/yr")
print(f"  Annual generation   : {res.annual_generation_kwh:,.0f} kWh")
print(f"  CAPEX               : Rp {res.capex_idr:,.0f}")
print(f"  Annual bill saving  : Rp {res.annual_bill_saving_idr:,.0f}")
print(f"  Payback             : {res.payback_years} years")
print(f"  IRR                 : {res.irr_pct}%")
print(f"  NPV                 : Rp {res.npv_idr:,.0f}")
print(f"  LCOE                : Rp {res.lcoe_idr_per_kwh}/kWh")
print(f"  Bankability score   : {res.bankability_score}/100")
print(f"  CO2 avoided         : {res.annual_co2_avoided_tonnes} t/yr "
      f"({res.lifetime_co2_avoided_tonnes} t over 25y)")
print(f"  Financing options   : {[o.label for o in res.financing_options]}")
print()

# --- Invariants ---
assert res.recommended_capacity_kwp > 0
assert res.capex_idr > 0
assert res.annual_bill_saving_idr > 0
assert len(res.financing_options) == 3  # cash, loan, PPA
assert len(res.cumulative_cashflow_cash_idr) == 26  # year 0..25
assert res.lcoe_idr_per_kwh < res.grid_tariff_idr_per_kwh, "solar LCOE should beat grid tariff"
assert res.annual_co2_avoided_tonnes > 0
print("✓ Estimate invariants hold (LCOE < grid tariff, 3 financing options, CO2 > 0)")

# --- Capacity-driven path ---
req2 = SolarEstimateRequest(desired_capacity_kwp=250, tariff_code="I-3/TM-200k+",
                            segment=CustomerSegment.industrial)
res2 = finance.analyze(req2, tariff_idr_per_kwh=1114.74)
assert res2.recommended_capacity_kwp == 250
assert res2.capex_per_kwp_idr == 11_500_000  # 100-1000 kWp tier
print(f"✓ Capacity-driven path OK (250 kWp industrial, payback={res2.payback_years}y)")

print()
print("=" * 60)
print("All Marketplace Tests Complete")
print("=" * 60)
