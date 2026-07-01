# Solara Optima — Improvement To-Do / Roadmap

Prioritized list of next improvements. Item 1 is the currently requested feature and
is spec'd in detail.

---

## 1. ✅ Live market parameters at startup (USD/IDR + carbon price)  — DONE

**Goal:** on every backend start (and on demand), fetch the **real-time USD/IDR rate**
and **carbon price**, so the *Market Parameters* on the **Settings** page and all
downstream economics (optimizer carbon cost, any USD conversions) reflect current values
— with a safe fallback to the configured defaults when offline.

**Why it matters:** `settings.CARBON_PRICE` already feeds the UC/ED optimizer objective,
and USD/IDR affects any USD-denominated CAPEX/benchmarks. Making them live keeps every
estimate current without manual edits.

**Design**
- New `backend/app/services/market_rates.py`:
  - `MarketRatesService` with pluggable providers and an in-memory cache
    (`value, source, fetched_at, is_live`) + TTL (e.g. 6 h).
  - **USD/IDR** provider: free, no-key FX API — e.g. `https://open.er-api.com/v6/latest/USD`
    → `rates.IDR`. Timeout 5 s; on failure fall back to `settings.USD_IDR_RATE`.
  - **Carbon price** provider: configurable. Default to Indonesia's statutory carbon-tax
    floor / IDXCarbon reference (fallback `settings.CARBON_PRICE`); make the source URL a
    config value so IDXCarbon (or an EU-ETS proxy) can be plugged in later.
  - All fetches wrapped in try/except → never block or crash startup.
- **Startup hook** in `main.py` (`@app.on_event("startup")`): kick off a non-blocking
  refresh; keep serving immediately with fallback values until it resolves.
- **Endpoint** `GET /api/v1/market/rates` → `{ usd_idr, carbon_price, sources,
  fetched_at, is_live }`. Add `POST /api/v1/market/rates/refresh` for a manual re-pull.
- Update the runtime market values used by the optimizer/finance from the cache (not just
  the static `settings`).
- **Frontend (Settings):** on load, `GET /market/rates`; prefill the *USD/IDR Rate* and
  *Carbon Price* fields; show a badge — `live • updated 5m ago` or `fallback (offline)`
  — and a small **Refresh** button.

**Config additions** (`core/config.py` / `.env`):
`ENABLE_LIVE_RATES=true`, `FX_RATES_URL=...`, `CARBON_PRICE_URL=...`, `RATES_TTL_HOURS=6`.

**Acceptance criteria**
- Backend starts fine with **no internet** (uses fallbacks, `is_live=false`).
- With internet, Settings shows a live USD/IDR that differs from the static default and a
  timestamp; **Refresh** re-pulls.
- Optimizer carbon cost uses the live carbon price when available.

---

## 2. ✅ Real weather / irradiance — DONE
Replaced clear-sky-only modeling with real **PVGIS ERA5 TMY** irradiance
(`services/weather_pvgis.py`), disk-cached per location with a TTL and a clear-sky
fallback when offline. Used by both the marketplace yield (full-year run) and the
`/forecast/solar` endpoint (TMY sliced to the requested window via the `pvgis_window`
source), with a Real/Clear-sky toggle in the Solar Forecast UI.

## 3. ✅ Location → yield wiring in the Marketplace — DONE
The Marketplace now sends the selected province's lat/lon (`PROVINCE_COORDS` in
`Marketplace.tsx`); the backend threads it into the PVGIS yield calc, so yield reflects
the chosen site, not just the Settings default.

## 4. ⚠️ Replace illustrative data with real, vetted data — MITIGATED
`data/installers.json`, `data/financiers.json`, and `data/pln_tariffs.json` are samples.
Provenance (`_source`/`_as_of`/per-item `verified`) now marks them as such, surfaced in
the API responses and via a "sample data" badge in the Marketplace UI; tariffs are
realistic PLN non-subsidized brackets. **Still required before go-live:** swap in real,
contracted partners and confirm the latest PLN tariff decree.

## 5. ✅ Resilience & UX — DONE
- React **error boundary** (`components/ErrorBoundary.tsx`) wraps the routed pages; a
  page crash now shows a friendly fallback with a "Try again" button instead of a white
  screen, and the sidebar stays mounted.
- **"Backend offline"** banner in Layout — polls the proxied `/api/v1/health` every 30s
  and shows a red banner when the backend is unreachable.

## 6. ✅ Frontend performance — DONE
Routes are `React.lazy`-loaded, Plotly is lazy-loaded via `<LazyPlot>`, and
`manualChunks` isolates the plotly bundle. Initial bundle ≈ 446 KB (was ~5.2 MB);
the ~4.7 MB plotly chunk loads only when a chart renders.

## 7. ⚠️ Leads → database + admin — MITIGATED
Leads still persist to `data/leads.jsonl`, but the store is now hardened
(`services/leads_store.py`: thread-safe atomic append + tolerant read/stats), with
per-IP rate limiting, email/name validation, and token-gated admin list/export
endpoints (`GET /admin/leads`, `/admin/leads/export`, `LEADS_ADMIN_TOKEN`). **Still
required:** move to Postgres (existing SQLAlchemy dep) + real auth + an admin UI.

## 8. ✅ Carbon-credit module (CIIC upside) — DONE
`services/carbon_credits.py` estimates issuable I-RECs (1 cert/MWh × an eligibility
factor), avoided tCO₂ (Indonesia grid factor), and indicative credit revenue (IDR + USD)
from solar generation. Surfaced per-quote in the estimate result + a UI panel, aggregated
in `/portfolio`, and via a standalone `GET /carbon/credits` endpoint. Config: `IREC_PRICE_USD`.
**Still open:** a real dMRV/registry integration and a live I-REC price feed.

## 9. Tests & CI — PARTIAL
`backend/test_marketplace_api.py` now also covers the carbon-credit block (estimate +
portfolio + `/carbon/credits` math), the `/api/v1/health` endpoint, and the
`/forecast/solar` `weather_source` param (clearsky + pvgis_window). **Still required:** a
frontend smoke test in CI, and deciding whether to port these script-style tests to pytest.
