# Solar Aggregation & Financing Marketplace

This document describes the marketplace layer added to Solara Optima and maps it to the
**Climate Impact Innovations Challenge (CIIC) 2026** submission form. Numbers here are
illustrative defaults produced by the engine — replace with your validated figures.

---

## 1. What it is

A rooftop-solar **go-to-market layer** on top of Solara Optima's pvlib generation engine.
It converts a prospective customer's PLN bill into:

1. a right-sized PV system (pvlib specific yield + self-consumption),
2. a **bankable** proposition — CAPEX, payback, IRR, NPV, LCOE, bankability score,
3. a **CO₂-avoided** figure (annual + 25-year lifetime),
4. a **financing menu** (cash / green loan / zero-CapEx PPA), and
5. **matched installer & financier partners** + lead capture, with a **portfolio**
   aggregation view.

**Track:** Energy Transition (renewable-energy adoption, efficient resource use).

---

## 2. How it works (reuses the existing engine)

```
PLN bill / target kWp
        │
        ▼
 finance.estimate_specific_yield()  ── uses SolarForecastService (pvlib clear-day × derate)
        │
        ▼
 finance.analyze()  ── sizing → self-consumption → CAPEX → 25y cashflow → payback/IRR/NPV/LCOE → CO₂
        │
        ├── /marketplace/estimate     (full result + financing menu + cashflow curve)
        ├── /marketplace/match        (installers filtered by kWp/region/segment; financiers by ticket)
        ├── /marketplace/quote-request(persist lead → data/leads.jsonl)
        └── /marketplace/portfolio    (aggregate leads → pipeline kWp & tCO₂)
```

Code: `backend/app/services/finance.py`, `backend/app/api/marketplace.py`,
`backend/app/models/marketplace_schemas.py`, `frontend/src/pages/Marketplace.tsx`.
Editable data: `backend/data/{pln_tariffs,installers,financiers}.json`.

---

## 3. Key assumptions (editable, illustrative)

| Assumption | Default | Where |
|---|---|---|
| Specific yield | pvlib clear-day × 0.72 derate (~1,400 kWh/kWp/yr) | `finance.py` |
| Grid emission factor | 0.85 kgCO₂/kWh (JAMALI interconnection) | `finance.py` |
| CAPEX | Rp 10–15 M/kWp (declining with scale) | `finance.py` |
| Self-consumption | 55% res / 75% commercial / 85% industrial | `finance.py` |
| PLN export credit | 0 (removed, Permen ESDM 2/2024) | `finance.py` |
| Degradation / O&M / escalation / discount | 0.5%/yr · 1% CAPEX · 3%/yr · 10% | `finance.py` |
| Loan / PPA | 11.5%/84mo/10% down · PPA 15% below tariff, 20y | `finance.py` |

> These are **not a financial guarantee**. The API returns them in `assumptions` for review.

---

## 4. CIIC form field mapping (draft answers)

**Project stage (TRL):** Working full-stack platform (FastAPI + React) with a live
sizing/financing engine and marketplace flows demonstrated end-to-end → **TRL 5–6**;
one paying pilot rooftop lifts it to TRL 7. *(State honestly what you have actually run.)*

**Proposed solution:** A rooftop-solar aggregation & financing marketplace for Indonesia.
Customers get an instant, pvlib-grounded, bankable savings + CO₂ estimate from their PLN
bill and are matched to installers and financing (cash / green loan / zero-CapEx PPA),
removing the two biggest adoption barriers: upfront cost and payback uncertainty.

**Impact (GHG):** Each 100 kWp rooftop avoids ~120–140 tCO₂/yr (grid factor 0.85
kgCO₂/kWh). The platform's leverage is aggregation: a pipeline of 1,000 such rooftops →
~130,000 tCO₂/yr avoided. Basis for future carbon-credit issuance (I-REC / avoided
grid emissions).

**Commercial applications / GTM:** (a) SME & commercial rooftops (C&I) as the beachhead —
strong daytime self-consumption → best payback; residential and industrial next.
(b) Revenue: lead-gen/referral fee from installers, arrangement fee from financiers, and
a SaaS/analytics fee; PPA option needs no customer CAPEX. Price point: free instant
estimate; monetize on conversion.

**Competitors / competing tech:** Individual EPC installers (Xurya, SUN Energy, Utomo,
ATW, etc.) selling their own systems; generic solar calculators; PLN grid tariff itself.
Financing is fragmented across banks/fintech.

**Competitive advantage:** Neutral marketplace (not tied to one installer) + a
physics-based (pvlib) engine + integrated financing + a real dispatch/optimization engine
underneath for C&I + storage cases. We aggregate demand and de-risk financing.

**Potential commercial partners:** Installers/EPCs (off-take of qualified leads), banks/
multifinance/fintech (loan origination), IPPs (PPA), and C&I off-takers (customers).
See `data/installers.json` / `data/financiers.json` (currently illustrative samples).

**Success looks like:** A funded pipeline of aggregated rooftops with measurable,
verifiable tCO₂ avoided and a repeatable installer+financier conversion funnel.

---

## 5. Try it

```bash
# Backend
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
# Frontend
cd frontend && npm run dev     # open http://localhost:3000 → "Solar Marketplace"

# Or hit the API directly:
curl -X POST localhost:8000/api/v1/marketplace/estimate \
  -H 'Content-Type: application/json' \
  -d '{"monthly_bill_idr":25000000,"tariff_code":"B-2/TR-6600-200k","segment":"commercial","roof_area_m2":800}'
```

Smoke test: `cd backend && python test_marketplace.py`.
