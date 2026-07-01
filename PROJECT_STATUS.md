# Solara Optima — Project Status

**Last updated:** 2026-07-01
**Purpose:** Rooftop-solar **aggregation & financing marketplace** for Indonesia, built on
top of a pvlib solar engine + UC/ED dispatch optimizer.
**Context:** Being prepared for the **Climate Impact Innovations Challenge (CIIC) 2026**
(Energy Transition track). Submission deadline: **8 July 2026**.

---

## 1. Snapshot

| Component | Status | Notes |
|---|---|---|
| Backend API (FastAPI) | ✅ Working | Imports clean, all routers mounted |
| UC/ED MILP optimizer | ✅ Working | Smoke test → Optimal (Rp 3.39M, ~1.9s) |
| Solar forecasting (pvlib) | ✅ Working | Clear-sky model; per-location |
| **Solar Marketplace (NEW)** | ✅ Working | Sizing + financing + CO₂ + matching + leads |
| **Live market rates (NEW)** | ✅ Working | USD/IDR live at startup; carbon = config fallback |
| Frontend (React/Vite) | ✅ Builds & runs | Verified in headless Chrome |
| Dashboard white-screen bug | ✅ Fixed | Was a pre-existing crash (see §4) |
| Demo assets | ✅ Done | `docs/DEMO.md` + screenshots |
| Real partner/tariff data | ⚠️ Illustrative | Sample data, must be replaced before go-live |

---

## 2. What this project is

The panels aren't the barrier to rooftop solar in Indonesia — **upfront cost and payback
uncertainty** are. Solara Optima removes both: enter a PLN bill (or target size) and get a
right-sized system, a **bankable** proposition (payback / IRR / NPV / LCOE + bankability
score), a quantified **tCO₂ avoided**, a **cash / loan / PPA** comparison, and **matched
installers & financiers** with lead capture and a portfolio (aggregation) view.

Underneath sits the original technical engine (pvlib generation + MILP UC/ED dispatch),
which also serves larger C&I and island-grid (solar+battery vs diesel) cases.

---

## 3. Architecture & key files

```
backend/app/
  main.py                      # app factory, router wiring, startup hooks
  core/config.py               # settings (location, market, live-rate config)
  services/
    optimizer.py               # UC/ED MILP (PuLP)
    solar_forecast.py          # pvlib generation
    finance.py                 # NEW: sizing, savings, payback/IRR/NPV/LCOE, CO₂, cash/loan/PPA
    market_rates.py            # NEW: live USD/IDR + carbon price, cache + fallback
  api/
    marketplace.py             # NEW: /estimate /installers /financiers /match /quote-request /portfolio /tariffs
    market.py                  # NEW: /rates /rates/refresh
    (optimize, forecast, generators, weather, location, pv_modules, ai_forecast)
  models/
    schemas.py, marketplace_schemas.py (NEW)
  data/
    pln_tariffs.json, installers.json, financiers.json (NEW, illustrative)
    generator_templates.json, cec_modules_cache.json
frontend/src/
  pages/Marketplace.tsx        # NEW: the hero flow
  pages/Settings.tsx           # UPDATED: live-rate badge + refresh
  pages/Dashboard.tsx          # FIXED: health-query crash
  components/Layout.tsx        # UPDATED: nav + smaller header
docs/
  MARKETPLACE.md               # feature + CIIC form field mapping
  DEMO.md                      # demo script, cities, scenarios
  ROADMAP.md                   # prioritized next steps
```

---

## 4. Work completed this cycle

1. **Cloned & ran** the repo; smoke-tested backend (optimizer + solar) and frontend build.
2. **Fixed a real frontend build bug** — missing Vite env types in `declarations.d.ts`.
3. **Built the #4 pivot** — Solar Aggregation & Financing Marketplace (finance engine,
   6 API endpoints, schemas, sample data, frontend page, nav/route, docs). Verified
   end-to-end in headless Chrome.
4. **Fixed the white-screen crash** — Dashboard's health check called `/` (not proxied in
   dev → returned SPA HTML → `healthData.location.latitude` threw → React unmounted). Made
   the query tolerant and sourced the banner location from the proxied endpoint. Pre-existing
   regression, not from the marketplace work.
5. **Shrank the sidebar header** font/size per feedback.
6. **Live market rates** — USD/IDR fetched from a free FX API at startup (+ manual refresh
   endpoint), cached with TTL and safe offline fallback; Settings shows a live/fallback
   badge and a Refresh button. Verified live (USD/IDR ≈ 17,934).
7. **Docs** — DEMO, MARKETPLACE, ROADMAP, and this status file.

---

## 5. Verified

- `backend/test_api.py` — optimizer + solar forecast pass.
- `backend/test_marketplace.py` — finance primitives + estimate invariants pass.
- Headless Chrome — Dashboard renders (no errors), Marketplace estimate→financing→match→quote flow works.
- Live `GET /api/v1/market/rates` returns a live USD/IDR with timestamp.
- `npm run build` — passes.

---

## 6. Known limitations (replace before submission/go-live)

- **Illustrative data:** `installers.json`, `financiers.json`, `pln_tariffs.json` are
  fictitious samples; techno-economic assumptions in `finance.py` are defaults.
- **Carbon price** has no free live IDR feed — falls back to config (Rp 50,000/tCO₂).
  Architecture supports plugging in IDXCarbon when a source is available.
- **Marketplace yield** uses the backend's configured location (set via Settings), not the
  per-request province (see ROADMAP §3).
- **Weather** is clear-sky only (no real irradiance API yet) — see ROADMAP §2.
- **Frontend bundle** ~5.2 MB (Plotly) — needs code-splitting (ROADMAP §6).
- **Leads** persist to `data/leads.jsonl` (no DB/auth yet).

---

## 7. Run

```bash
# Backend
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
# Frontend
cd frontend && npm run dev            # http://localhost:3000
```
Both must run: pages load without the backend, but data calls will fail quietly.

---

## 8. Next steps
See [`docs/ROADMAP.md`](docs/ROADMAP.md). Immediate priorities: replace illustrative
data with real partners/tariffs, wire province→yield, and (for the pitch) fill the CIIC
form fields using [`docs/MARKETPLACE.md`](docs/MARKETPLACE.md).
