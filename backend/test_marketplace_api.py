#!/usr/bin/env python3
"""API-level smoke test for the marketplace endpoints.

Exercises the workaround changes: data provenance in responses, PVGIS-driven
yield when site coords are supplied, hardened leads store, token-gated admin
endpoints, per-IP rate limiting, and email/name validation.
"""

import os
import sys

# Configure an admin token before the app/settings are imported.
os.environ.setdefault("LEADS_ADMIN_TOKEN", "test-secret")

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)
fail = []


def check(cond, msg):
    print(f"  {'✓' if cond else '✗'} {msg}")
    if not cond:
        fail.append(msg)


print("=" * 60)
print("Solara Optima - Marketplace API Test Suite")
print("=" * 60)

# --- Tariffs + provenance in message ---
r = client.get("/api/v1/marketplace/tariffs")
check(r.status_code == 200, f"GET /tariffs -> 200 (got {r.status_code})")
check(
    "verified" in (r.json().get("message") or "") or "sample" in (r.json().get("message") or ""),
    "tariffs response carries a provenance tag",
)
check(len(r.json()["data"]) >= 5, "tariffs list populated")

# --- Estimate with site coords -> weather_source surfaced ---
r = client.post(
    "/api/v1/marketplace/estimate",
    json={
        "monthly_bill_idr": 25_000_000,
        "tariff_code": "B-2/TR-6600-200k",
        "segment": "commercial",
        "roof_area_m2": 800,
        "latitude": -6.2088,
        "longitude": 106.8456,
    },
)
check(r.status_code == 200, f"POST /estimate w/ coords -> 200 (got {r.status_code})")
data = r.json()["data"]
ws = data["assumptions"].get("weather_source", "")
check(bool(ws), f"assumptions.weather_source present ({ws!r})")
check(data["annual_co2_avoided_tonnes"] > 0, "estimate CO2 avoided > 0")
check(data["lcoe_idr_per_kwh"] < data["grid_tariff_idr_per_kwh"], "LCOE < grid tariff")

# --- Match + sample-data note ---
r = client.post(
    "/api/v1/marketplace/match",
    json={"capacity_kwp": 100, "segment": "commercial", "region": "Jawa Barat"},
)
check(r.status_code == 200, "POST /match -> 200")
check("sample" in (r.json().get("message") or ""), "match response notes sample partner data")

# --- Quote: valid lead ---
r = client.post(
    "/api/v1/marketplace/quote-request",
    json={"name": "Test User", "email": "User@Example.com", "segment": "commercial"},
)
check(r.status_code == 200, f"valid quote -> 200 (got {r.status_code})")
check(r.json()["data"]["lead_id"].startswith("lead-"), "lead_id returned")

# --- Quote: invalid email -> 422 ---
r = client.post(
    "/api/v1/marketplace/quote-request",
    json={"name": "Bad", "email": "not-an-email"},
)
check(r.status_code == 422, f"invalid email -> 422 (got {r.status_code})")

# --- Quote: blank name -> 422 ---
r = client.post(
    "/api/v1/marketplace/quote-request",
    json={"name": "   ", "email": "x@y.com"},
)
check(r.status_code == 422, f"blank name -> 422 (got {r.status_code})")

# --- Admin gating ---
saved = settings.LEADS_ADMIN_TOKEN
settings.LEADS_ADMIN_TOKEN = None
r = client.get("/api/v1/marketplace/admin/leads")
check(r.status_code == 503, f"admin disabled (no token) -> 503 (got {r.status_code})")
settings.LEADS_ADMIN_TOKEN = saved

r = client.get("/api/v1/marketplace/admin/leads")
check(r.status_code == 403, f"admin no token -> 403 (got {r.status_code})")
r = client.get(
    "/api/v1/marketplace/admin/leads", headers={"X-Admin-Token": "wrong"}
)
check(r.status_code == 403, f"admin wrong token -> 403 (got {r.status_code})")
r = client.get(
    "/api/v1/marketplace/admin/leads", headers={"X-Admin-Token": "test-secret"}
)
check(r.status_code == 200, f"admin right token -> 200 (got {r.status_code})")
check(r.json()["data"]["count"] >= 1, "admin can see stored leads")

# --- Export ---
r = client.get(
    "/api/v1/marketplace/admin/leads/export", headers={"X-Admin-Token": "test-secret"}
)
check(r.status_code == 200, f"export -> 200 (got {r.status_code})")
check(
    "attachment" in r.headers.get("content-disposition", ""),
    "export returns a JSON attachment",
)

# --- Portfolio sees the lead ---
r = client.get("/api/v1/marketplace/portfolio")
check(r.status_code == 200, "GET /portfolio -> 200")
check(r.json()["data"]["total_leads"] >= 1, "portfolio aggregates stored leads")

# --- Carbon-credit / I-REC block on the estimate ---
cc = data.get("carbon_credits", {})
check(bool(cc), "estimate result carries a carbon_credits block")
check(cc.get("irecs_issuable", 0) > 0, f"estimate I-RECs issuable > 0 ({cc.get('irecs_issuable')})")
check(cc.get("avoided_co2_tonnes", 0) > 0, "estimate avoided CO2 > 0 (carbon block)")
check(cc.get("indicative_revenue_idr", 0) > 0, "estimate indicative revenue > 0")

# --- Portfolio carbon_credits block (aggregation story) ---
check("carbon_credits" in r.json()["data"], "portfolio carries a carbon_credits block")

# --- Standalone /carbon/credits endpoint (10 MWh -> 9.5 I-RECs, 8.5 tCO2) ---
r2 = client.get("/api/v1/marketplace/carbon/credits", params={"annual_generation_kwh": 10000})
check(r2.status_code == 200, f"GET /carbon/credits -> 200 (got {r2.status_code})")
ccd = r2.json()["data"]
check(abs(ccd["irecs_issuable"] - 9.5) < 0.05, f"carbon/credits I-RECs == 9.5 (got {ccd['irecs_issuable']})")
check(abs(ccd["avoided_co2_tonnes"] - 8.5) < 0.05, f"carbon/credits avoided CO2 == 8.5 (got {ccd['avoided_co2_tonnes']})")
check(abs(ccd["indicative_revenue_usd"] - 14.25) < 0.05, f"carbon/credits revenue_usd == 14.25 (got {ccd['indicative_revenue_usd']})")

# --- /api/v1/health (proxied health for the offline banner) ---
r3 = client.get("/api/v1/health")
check(r3.status_code == 200, f"GET /api/v1/health -> 200 (got {r3.status_code})")
check(r3.json()["status"] == "ok", "/api/v1/health status == ok")

# --- /forecast/solar accepts weather_source; returns the requested horizon ---
rf = client.get(
    "/api/v1/forecast/solar",
    params={"capacity": 10, "hours": 24, "weather_source": "clearsky"},
)
check(rf.status_code == 200, f"GET /forecast/solar clearsky -> 200 (got {rf.status_code})")
check(len(rf.json()["data"]["generation"]) >= 24, "forecast clearsky returns >=24 points")
rfp = client.get(
    "/api/v1/forecast/solar",
    params={"capacity": 10, "hours": 24, "weather_source": "pvgis_window"},
)
check(rfp.status_code == 200, f"GET /forecast/solar pvgis_window -> 200 (got {rfp.status_code})")
check(
    len(rfp.json()["data"]["generation"]) >= 24,
    "forecast pvgis_window returns >=24 points (PVGIS or clear-sky fallback)",
)

# --- Rate limiting (burst -> at least one 429) ---
statuses = []
for i in range(8):
    rr = client.post(
        "/api/v1/marketplace/quote-request",
        json={"name": f"Burst {i}", "email": f"burst{i}@example.com"},
    )
    statuses.append(rr.status_code)
check(429 in statuses, f"rate limit triggered (statuses={sorted(set(statuses))})")

print("=" * 60)
if fail:
    print(f"FAIL: {len(fail)} check(s) failed: {fail}")
    sys.exit(1)
print("All Marketplace API tests passed")