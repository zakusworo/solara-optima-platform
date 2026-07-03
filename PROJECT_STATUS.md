# Solara Optima — Project Status

**Last updated:** 2026-07-03
**Purpose:** Rooftop-solar **aggregation & financing marketplace** for Indonesia, built on
top of a pvlib solar engine + UC/ED dispatch optimizer.
**Stack:** FastAPI + pvlib + PuLP/CBC backend, React 18 + Vite + TypeScript frontend.
**Context:** Being prepared for the **Climate Impact Innovations Challenge (CIIC) 2026**
(Energy Transition track). Submission deadline: **8 July 2026**.

> All commits are by **Zulfikar Aji Kusworo &lt;greataji13@gmail.com&gt;** — single
> committer, no co-authors. Current default branch `main` mirrors `origin/main`.

---

## 1. Snapshot

| Component | Status | Notes |
|---|---|---|
| Backend API (FastAPI) | ✅ Working | Imports clean, all routers mounted |
| UC/ED MILP optimizer | ✅ Working | Smoke test → Optimal (Rp 3.39M, ~1.9s); fleet from shared store drives dispatch |
| Solar forecasting (pvlib) | ✅ Working | Clear-sky **and** real PVGIS TMY; per-location; auto forecast anchored to local midnight |
| PV module DB (CEC) | ✅ Working | 21,677 real panels; manufacturer/technology dropdowns populated from live DB |
| **Solar Marketplace** | ✅ Working | Sizing + financing + CO₂ + matching + leads |
| **Live market rates** | ✅ Working | Real-time USD/IDR + carbon price at startup and on demand, offline fallback |
| **Real irradiance (PVGIS)** | ✅ Working | ERA5 TMY for yield + /forecast; clear-sky fallback |
| **Carbon credits (I-REC)** | ✅ Working | Per-quote + portfolio I-REC / avoided-CO₂ / revenue |
| **Error boundary + offline banner** | ✅ Working | Friendly crash fallback; `/api/v1/health` banner |
| **Frontend bundle split** | ✅ Working | ~446 KB initial (was 5.2 MB); Plotly on-demand |
| Frontend (React/Vite) | ✅ Builds & runs | Route-level lazy + `manualChunks` |
| Dashboard white-screen bug | ✅ Fixed | Was a pre-existing crash (see §4) |
| Demo assets | ✅ Done | `docs/DEMO.md` + screenshots |
| Settings persistence | ⚠️ Partial | `Save` persists **location** only (see §6a) |
| Real partner/tariff data | ⚠️ Sample (labeled) | Provenance + UI badge; replace before go-live |
| Result store | ⚠️ In-process | `OrderedDict`, single worker; Redis when scaling (see §6a) |

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

## 4c. Carbon-credit + safety cycle (2026-07-01)

1. **Carbon-credit module** — `services/carbon_credits.py` estimates I-RECs (1 cert/MWh
   × eligibility), avoided tCO₂, and indicative credit revenue (IDR + USD). Surfaced
   per-quote in the estimate result + a UI panel, aggregated in `/portfolio`, and via
   `GET /carbon/credits`. Targets the CIIC carbon-credit award.
2. **Real irradiance in /forecast** — new `pvgis_window` weather source slices the PVGIS
   TMY to the requested window (local-time aligned); the Solar Forecast page defaults to
   real irradiance with a Real/Clear-sky toggle.
3. **Error boundary** — `components/ErrorBoundary.tsx` wraps the routed pages so a crash
   shows a friendly fallback (sidebar stays mounted) instead of a white screen.
4. **Backend-offline banner** — Layout polls the proxied `/api/v1/health` and shows a red
   banner when the backend is unreachable.

---

## 4d. Fix cycle (2026-07-01, late) — forecast + dispatch wiring

1. `ce4d546` **PV module manufacturer dropdown** — now uses real CEC manufacturers
   (dynamic from the live DB + case-insensitive filter; placeholder row dropped).
2. `12a8ba4` **Shared fleet store drives optimization dispatch** — the generator fleet
   configured on the **Generators** page (preset/template buttons wired, editable fleet
   + solar/battery) is what the Optimization page sends; per-generator chart series are
   rendered from the real result instead of hardcoded values.
3. `e8c929b` **Auto solar forecast anchored to local midnight** — was starting at
   `now()`, shifting solar ~7h (solar at night, zero at midday); now peaks at noon.

---

## 5. Verified

- `backend/test_api.py` — optimizer + solar forecast pass.
- `backend/test_marketplace.py` — finance primitives + estimate invariants pass
  (re-run 2026-07-03: all pass; payback 7.5y, IRR 14%, bankability 72/100).
- `backend/test_marketplace_api.py` — provenance, PVGIS-with-coords, leads store,
  admin gating (503/403/200), rate limit (429), email/name validation pass.
- PVGIS yields verified (Jakarta 1412, Denpasar 1544, Medan 1310 kWh/kWp/yr) with
  disk-cache hit on repeat; clear-sky fallback confirmed when offline.
- Headless Chrome — Dashboard renders (no errors), Marketplace estimate→financing→match→quote flow works.
- Live `GET /api/v1/market/rates` returns a live USD/IDR with timestamp.
- `backend/test_marketplace_api.py` now also asserts the carbon_credits block (estimate +
  portfolio), `/carbon/credits` math (9.5 I-RECs / 8.5 tCO₂ for 10 MWh), `/api/v1/health`,
  and the `/forecast/solar` `weather_source` param (clearsky + pvgis_window).
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
| 6 | Carbon price / credit monetisation | ⚠️ **Partially addressed** — an I-REC carbon-credit estimate (issuable certs, avoided tCO₂, indicative revenue) is now surfaced per-quote and in the portfolio; the I-REC unit price is a configurable default (USD). **Still pending:** a live I-REC/IDXCarbon price feed and a real dMRV/registry integration. |

### 6a. Open gaps (not yet worked around)

- **Settings persistence** — `Save` persists **location** only. USD/IDR + carbon price
  are live-fed (backend is source of truth), but solver / PV-default / override fields
  have no backend persistence endpoint and are local-only. Needs a `/settings` save
  endpoint to make them stick.
- **Result store** — in-process `OrderedDict` (single worker); replace with Redis when
  scaling horizontally.

---

## 7. Run

```bash
# Backend (FastAPI + uvicorn, with live reload)
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload --port 8000      # health: GET /api/v1/health

# Frontend (Vite dev server on :3000, proxies /api → :8000)
cd frontend && npm run dev                      # open http://localhost:3000
```
Both must run: pages load without the backend, but data calls will fail quietly.

Smoke test: `cd backend && python test_marketplace.py`.
Demo guide: [`docs/DEMO.md`](docs/DEMO.md). Marketplace spec: [`docs/MARKETPLACE.md`](docs/MARKETPLACE.md).

---

## 8. Next steps

See [`docs/ROADMAP.md`](docs/ROADMAP.md). Remaining priorities: replace sample partner
data with real contracted partners/tariffs, add a live carbon-price source (IDXCarbon),
move leads to a DB + auth (ROADMAP §7), add a `/settings` save endpoint, and (for the
pitch) fill the CIIC form fields using [`docs/MARKETPLACE.md`](docs/MARKETPLACE.md).

---

## 9. Commit history

Reverse-chronological. All commits by Zulfikar Aji Kusworo.

| Date       | Commit   | Message |
|------------|----------|---------|
| 2026-07-01 | `19364d0` | docs: add project-status.md with current status and full commit history |
| 2026-07-01 | `e8c929b` | fix(optimize): anchor auto solar forecast to local midnight |
| 2026-07-01 | `12a8ba4` | feat(generators): shared fleet store drives optimization dispatch |
| 2026-07-01 | `ce4d546` | fix(forecast): PV module manufacturer dropdown uses real CEC manufacturers |
| 2026-07-01 | `023c750` | feat: carbon-credit (I-REC) module + real PVGIS in /forecast + demo safety |
| 2026-07-01 | `bbca64f` | feat: workarounds for known limitations 1-5 (PVGIS, province->yield, bundle split, leads, provenance) |
| 2026-07-01 | `9f30c0a` | feat: solar aggregation & financing marketplace + live market rates |
| 2026-05-10 | `0c97323` | fix(ci): unblock CI by removing dead dep and correcting trivy tag |
| 2026-05-10 | `6dbda5b` | docs: add May 2026 security & quality hardening to Recent Updates |
| 2026-05-10 | `f1cba63` | fix(compose): add healthchecks for all services |
| 2026-05-10 | `6389e26` | fix: resolve MEDIUM audit issues |
| 2026-05-10 | `53d0e81` | docs: remove institutional affiliation from README, QUICKSTART, setup.sh |
| 2026-05-10 | `e9b67bd` | fix(security,ci): resolve HIGH severity audit issues + harden CI |
| 2026-05-10 | `bfc3d9e` | fix(critical): resolve 6 critical issues from audit |
| 2026-04-24 | `7000e67` | docs: Major README overhaul with new features — PV module DB, geolocation, BESS fix, API table, architecture diagram |
| 2026-04-24 | `4e3213c` | feat: PV module DB, location auto-detect, hourly load editor, BESS fix |
| 2026-04-23 | `10669b5` | feat(location): Add interactive map + geocoding |
| 2026-04-23 | `ddae488` | fix(ui): Replace `<a>` tags with `<Link>` for SPA navigation in Dashboard |
| 2026-04-23 | `13d4f5c` | fix(frontend): Fix build errors - rename config to .cjs, add tsconfig.node.json, add plotly declarations, relax strict TS |
| 2026-04-23 | `affaf68` | refactor: Rename all Solar UC/ED references to Solara Optima Platform |
| 2026-04-19 | `a72c884` | Update Ollama models: Switch all references to qwen3.5 |
| 2026-04-19 | `71a0c96` | Update DOI to 10.5281/zenodo.19653510 |
| 2026-04-19 | `7f30bd3` | Update README: Add screenshot and update author affiliation |
| 2026-04-19 | `004931d` | Add dashboard screenshot to docs |
| 2026-04-19 | `ead4366` | Update web demo: Switch from green to blue color scheme |
| 2026-04-19 | `d3b1a4f` | Fix CI/CD pipeline: simplify jobs and add error tolerance |
| 2026-04-19 | `07c317a` | Update: MIT License, repo description, and switch to Qwen3.5 |
| 2026-04-19 | `d737d03` | Add GitHub Actions CI/CD pipeline |
| 2026-04-19 | `a6cf936` | Initial commit: Solara Optima Platform v1.0.0 |

> Regenerate the table with:
> `git log --pretty=format:'| %ad | \`%h\` | %s |' --date=format:'%Y-%m-%d'`
