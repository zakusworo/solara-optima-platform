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
| Solar forecasting (pvlib) | ✅ Working | Clear-sky **and** real PVGIS TMY; per-location |
| **Solar Marketplace** | ✅ Working | Sizing + financing + CO₂ + matching + leads |
| **Live market rates** | ✅ Working | USD/IDR live at startup; carbon = config fallback |
| **Real irradiance (PVGIS)** | ✅ Working | ERA5 TMY per site; clear-sky fallback; disk-cached |
| **Frontend bundle split** | ✅ Working | ~446 KB initial (was 5.2 MB); Plotly on-demand |
| Frontend (React/Vite) | ✅ Builds & runs | Route-level lazy + `manualChunks` |
| Dashboard white-screen bug | ✅ Fixed | Was a pre-existing crash (see §4) |
| Demo assets | ✅ Done | `docs/DEMO.md` + screenshots |
| Real partner/tariff data | ⚠️ Sample (labeled) | Provenance + UI badge; replace before go-live |

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

## 4b. Workaround cycle (2026-07-01) — Known limitations 1–5

1. **Real irradiance (PVGIS)** — `services/weather_pvgis.py` fetches an ERA5 TMY per
   site (free, no key), disk-cached with TTL; `solar_forecast` + `finance` use it for
   site-specific, cloud-adjusted yield with clear-sky fallback. Default-location TMY
   is pre-fetched at startup.
2. **Province → yield** — the Marketplace sends the selected province's lat/lon; the
   backend threads it into the PVGIS yield calc, so estimates are per-site.
3. **Bundle split** — `React.lazy` routes + `<LazyPlot>` (lazy `react-plotly.js`) +
   `manualChunks`; initial bundle ≈ 446 KB, Plotly loaded on-demand.
4. **Leads hardened** — `services/leads_store.py` (thread-safe atomic append + stats),
   per-IP rate limit, email/name validation, token-gated `/admin/leads` + `/export`.
5. **Data provenance** — `_source`/`_as_of`/per-item `verified` in the data files,
   surfaced in API responses + a "sample data" badge in the Marketplace UI.

---

## 5. Verified

- `backend/test_api.py` — optimizer + solar forecast pass.
- `backend/test_marketplace.py` — finance primitives + estimate invariants pass.
- `backend/test_marketplace_api.py` — provenance, PVGIS-with-coords, leads store,
  admin gating (503/403/200), rate limit (429), email/name validation pass.
- PVGIS yields verified (Jakarta 1412, Denpasar 1544, Medan 1310 kWh/kWp/yr) with
  disk-cache hit on repeat; clear-sky fallback confirmed when offline.
- Headless Chrome — Dashboard renders (no errors), Marketplace estimate→financing→match→quote flow works.
- Live `GET /api/v1/market/rates` returns a live USD/IDR with timestamp.
- `npm run build` — passes; initial bundle ≈ 446 KB, Plotly in an on-demand chunk.

---

## 6. Known limitations & mitigations

| # | Limitation | Status after the workaround cycle |
|---|---|---|
| 1 | Illustrative partner/tariff data | ⚠️ **Mitigated** — provenance (`_source`/`_as_of`/per-item `verified`) added to the data files and surfaced in API responses; a "sample data" badge in the Marketplace UI. Tariffs are realistic PLN non-subsidized brackets. Real contracted partners still required before go-live. |
| 2 | Clear-sky-only weather | ✅ **Addressed** — marketplace yield now uses a real **PVGIS (ERA5) satellite TMY** when site coordinates are supplied (cloud-adjusted, no derate), with clear-sky fallback and a per-location disk cache. `/forecast` still defaults to clear-sky. |
| 3 | Province → yield not wired | ✅ **Addressed** — the frontend sends the selected province's lat/lon; the backend threads it into the PVGIS yield calc, so estimates are site-specific. |
| 4 | 5.2 MB frontend bundle (Plotly) | ✅ **Addressed** — routes are `React.lazy`-loaded, Plotly is lazy-loaded via `<LazyPlot>`, and `manualChunks` isolates it. Initial bundle ≈ 446 KB (was 5,235 KB); Plotly loads only when a chart renders. |
| 5 | Leads to `leads.jsonl`, no DB/auth | ⚠️ **Mitigated** — hardened thread-safe atomic store, per-IP rate limiting, email/name validation, and token-gated admin list/export endpoints (`LEADS_ADMIN_TOKEN`). Full DB + auth still pending (ROADMAP §7). |
| 6 | Carbon price has no live IDR feed | ⚠️ Unchanged — falls back to config (Rp 50,000/tCO₂); architecture ready for IDXCarbon when a source exists. |

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
See [`docs/ROADMAP.md`](docs/ROADMAP.md). Remaining priorities: replace sample partner
data with real contracted partners/tariffs, add a live carbon-price source (IDXCarbon),
move leads to a DB + auth (ROADMAP §7), wire real weather into the `/forecast` endpoint,
and (for the pitch) fill the CIIC form fields using [`docs/MARKETPLACE.md`](docs/MARKETPLACE.md).
