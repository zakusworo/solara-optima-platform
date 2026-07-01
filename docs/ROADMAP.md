# Solara Optima — Improvement To-Do / Roadmap

Prioritized list of next improvements. Item 1 is the currently requested feature and
is spec'd in detail.

---

## 1. ⭐ Live market parameters at startup (USD/IDR + carbon price)  — REQUESTED

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

## 2. Real weather / irradiance (accuracy)
Replace clear-sky-only modeling with real data — PVGIS TMY, NASA POWER, or BMKG — so
specific yield reflects actual cloud cover per site. Cache TMY per location.

## 3. Location → yield wiring in the Marketplace
The Marketplace estimate currently uses the backend default location for specific yield.
Pass the selected city's lat/lon from the form so yield reflects the chosen city, not just
the Settings default.

## 4. Replace illustrative data with real, vetted data
`data/installers.json`, `data/financiers.json`, and `data/pln_tariffs.json` are samples.
Swap in real, contracted partners and the latest PLN tariff decree before go-live.

## 5. Resilience & UX
- Add a React **error boundary** (the Dashboard crash we fixed would have shown a friendly
  message instead of a white screen).
- Add a **"backend offline"** banner when `/health` is unreachable.

## 6. Frontend performance
The bundle is ~5.2 MB (Plotly dominates). Code-split routes and lazy-load Plotly
(`React.lazy` + `manualChunks`) to cut initial load.

## 7. Leads → database + admin
Move leads from `data/leads.jsonl` to a real DB (Postgres via the existing SQLAlchemy dep),
add auth, and build a simple admin/portfolio dashboard.

## 8. Carbon-credit module (CIIC upside)
Add a dMRV / I-REC hook: from aggregated portfolio generation, estimate issuable credits
and indicative revenue — directly targeting the CIIC carbon-credit award.

## 9. Tests & CI
Add pytest coverage for the marketplace endpoints and a frontend smoke test in CI.
