# Solara Optima Platform

**AI-Enhanced Unit Commitment & Economic Dispatch for Renewable-Integrated Power Systems**

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19653510.svg)](https://doi.org/10.5281/zenodo.19653510)

A platform for accelerating **rooftop solar adoption in Indonesia**. On top of a
physics-based **solar PV** engine (pvlib) and a **UC/ED dispatch optimizer**, Solara
Optima adds a **Solar Aggregation & Financing Marketplace**: it turns a customer's PLN
bill into a right-sized system, a **bankable savings/ROI proposition**, a quantified
**CO₂-reduction** figure, and matches the project to **installers and financing**
(cash / green loan / zero-CapEx PPA).

**Repository**: https://github.com/zakusworo/solara-optima-platform

---

## Solar Aggregation & Financing Marketplace

> **CIIC 2026 track: Energy Transition** — promoting renewable-energy adoption and
> efficient resource use, with measurable GHG reduction.

The barrier to rooftop solar in Indonesia is rarely the panels — it's **upfront cost and
uncertainty about payback**. This layer removes both:

- **Bill → system**: enter a monthly PLN bill (or target kWp), get a right-sized system
  using pvlib-derived specific yield and self-consumption-aware savings (PLN export
  credit removed per Permen ESDM 2/2024 is modeled).
- **Bankable economics**: CAPEX, payback, IRR, NPV, LCOE and a **bankability score**,
  plus a side-by-side **cash / loan / PPA** comparison with 25-year cashflows.
- **Climate impact**: annual & lifetime **tCO₂ avoided** (grid emission factor) — the
  metric CIIC scores and the basis for carbon-credit potential.
- **Marketplace**: matches the sized project to **installer** and **financier** partners
  and captures **leads**; a **portfolio** view aggregates many rooftops into one
  investable pipeline.
- **Carbon credits (I-REC)**: issuable certificates (1/MWh × eligibility), avoided tCO₂
  (Indonesia grid factor), and indicative credit revenue — per quote, per portfolio, and
  via a standalone endpoint.

Open the **Solar Marketplace** page in the app, or see [`docs/MARKETPLACE.md`](docs/MARKETPLACE.md)
for the full field-by-field CIIC mapping. Marketplace API lives under
`/api/v1/marketplace/*`.

**Docs:** [`docs/DEMO.md`](docs/DEMO.md) — step-by-step demo script, demo cities, and
ready-made scenarios · [`docs/ROADMAP.md`](docs/ROADMAP.md) — planned improvements ·
[`PROJECT_STATUS.md`](PROJECT_STATUS.md) — current status, verification log, and full
commit history.

---

## Highlights

- **MILP Solver** (PuLP/CBC) for mixed-integer optimal dispatch with generator constraints, ramp rates, min uptime/downtime — the fleet configured on the **Generators** page drives the dispatch run via a shared store
- **pvlib Integration** for physics-based solar generation forecasting — real **PVGIS (ERA5) satellite TMY** per site with clear-sky fallback, auto forecast anchored to local midnight
- **PV Module Database** with 21,677 real CEC modules — search, filter, and auto-scale plant capacity by module selection; manufacturer/technology dropdowns populated from the live DB
- **Solar Marketplace & Financing** — PLN bill → sized system → bankability (payback/IRR/NPV/LCOE) → installer/financier matching → leads & portfolio
- **Carbon Credits (I-REC)** — issuable certificates, avoided tCO₂, and indicative revenue per quote and portfolio
- **Live Market Rates** — real-time USD/IDR + carbon price at startup and on demand, cached with offline fallback
- **Battery Storage (BESS)** with binary charge/discharge mode, SOC tracking, and efficiency losses
- **Multi-Agent AI Forecasting** via Ollama LLMs for load and solar prediction
- **Auto Geolocation** — browser GPS → OpenStreetMap reverse geocoding → fallback to backend config
- **Hourly Load Profile Editor** with live totals, peak/average stats, and interactive visual feedback
- **Indonesian Market Mode** with IDR currency, PLN tariff structures, and carbon pricing

---

## Features

### Core Optimization (MILP)

| Feature | Description |
|---------|-------------|
| **UC/ED Solver** | MILP formulation via PuLP — schedules generator on/off and dispatch levels |
| **Generator Constraints** | Min/max output, ramp-up/down limits, min uptime/downtime, startup/shutdown costs |
| **Solar PV Dispatch** | Forecasted solar generation injected as negative load into UC/ED |
| **BESS Scheduling** | Binary mode charge/discharge with SOC dynamics and round-trip efficiency |
| **Reserve Requirements** | Spinning, operating, and uncertainty reserves enforced per period |
| **Multi-Period Rolling Horizon** | 24h+ optimization with time-of-use tariff awareness |

### Solar PV Forecasting

| Feature | Description |
|---------|-------------|
| **pvlib Physics Engine** | Position-of-sun, irradiance transposition, temperature derating, DC-DC modeling |
| **Location-Aware** | Defaults to Bandung, Indonesia (-6.9147 S, 107.6098 E, 768 m) with auto browser geolocation fallback |
| **Southern Hemisphere Optimized** | Azimuth 0 = North-facing (correct for Indonesia) |
| **Override Parameters** | Query-time overrides for latitude, longitude, altitude, tilt, azimuth |
| **Real Irradiance (PVGIS)** | ERA5 satellite TMY per site (free, no key), disk-cached with TTL; `weather_source=pvgis_window` slices the TMY to the requested window, clear-sky fallback |
| **Hourly Resolution** | Up to 168h forecast horizon |

### PV Module Database

| Feature | Description |
|---------|-------------|
| **CEC Module Cache** | 21,677 commercial PV modules cached locally from the NREL SAM CEC database |
| **Search & Filter** | By manufacturer, technology (Mono/Multi/CdTe), power range, text search — dropdowns populated dynamically from the live DB |
| **Module Selection** | Click-to-select from browsable table; auto-suggests plant capacity based on module wattage |
| **Manual Entry** | Override with custom STC/PTC, efficiency, Vmp, Imp, temperature coefficients |
| **Auto-Scaling** | Enter desired plant capacity (kW) — frontend calculates module count and total output |

### Marketplace, Financing & Carbon

| Feature | Description |
|---------|-------------|
| **Bill → System Sizing** | Monthly PLN bill (or target kWp) → right-sized system via PVGIS-derived specific yield, self-consumption-aware savings (Permen ESDM 2/2024 modeled) |
| **Bankable Economics** | CAPEX, payback, IRR, NPV, LCOE, bankability score; cash / green loan / zero-CapEx PPA with 25-year cashflows |
| **Carbon Credits (I-REC)** | 1 certificate/MWh × eligibility, avoided tCO₂ (grid factor 0.85 kgCO₂/kWh), indicative revenue in IDR + USD |
| **Partner Matching** | Installer + financier matching with lead capture; hardened leads store (rate limit, validation, token-gated admin) |
| **Portfolio Aggregation** | Many rooftops → one investable pipeline (capacity, CO₂, I-REC aggregate) |
| **Live Market Rates** | USD/IDR + carbon price fetched at startup, TTL cache, manual refresh, offline fallback |
| **Data Provenance** | `_source`/`_as_of`/`verified` flags on sample partner/tariff data, surfaced in the API and a UI badge |

### AI Forecasting Agents

| Feature | Description |
|---------|-------------|
| **Ollama Integration** | Local LLM agents (Qwen3.5, accessible via `/api/v1/ai/*`) |
| **Load Forecasting** | LLM-based pattern recognition on historical load data |
| **Solar Forecasting** | AI-augmented correction to physics-based pvlib forecasts |
| **Fallback Mode** | Graceful degradation to statistical methods when Ollama unavailable |

### Frontend UX

| Feature | Description |
|---------|-------------|
| **Auto Location Detection** | `navigator.geolocation` → Nominatim reverse geocode → backend fallback |
| **Hourly Load Editor** | 24 editable cells with live daily totals, peak, and average kW |
| **Interactive Plotly Charts** | Generation forecasts, load profiles, dispatch schedules, temperature curves — lazy-loaded via `<LazyPlot>` |
| **Shared Fleet Store** | Generator fleet configured on the Generators page (presets/templates, solar/battery) drives the Optimization run and Dashboard |
| **Lean Bundle** | `React.lazy` routes + `manualChunks` — ~446 KB initial (was 5.2 MB), Plotly on demand |
| **Demo Safety** | Error boundary with friendly crash fallback + backend-offline banner (`/api/v1/health` poll) |
| **Responsive Layout** | Tailwind CSS with mobile sidebar, presentation-mode typography |
| **Real-Time Status** | Generation status, cost summaries, capacity factors |

---

## Architecture

```
                    +------------------+
                    |   React + Vite   |
                    |   (Frontend)     |
                    +--------+---------+
                             |
           +-----------------+------------------+
           |                                    |
    +------v-------+     +----------+     +------v-------+
    |   Plotly     |     |  Axios   |     |  Leaflet   |
    |  Charts      |     |  REST    |     |   Map      |
    +--------------+     +----+-----+     +------------+
                              |
                    +---------v-----------+
                    |    FastAPI (8000)   |
                    |    Python Backend   |
                    +----+----------+-----+
                         |          |
            +------------+          +------------+
            |                                    |
     +------v-------+                    +------v-------+
     |   UC/ED      |                    |  Solar/Weather |
     |   Optimizer  |                    |  Forecasting   |
     |   (PuLP)     |                    |  (pvlib)       |
     +--------------+                    +------+---------+
                                                |
                                   +------------+------------+
                                   |                         |
                            +------v-----+           +------v------+
                            |    CEC     |           |   Ollama    |
                            |  Module DB |           |   (LLMs)    |
                            +------------+           +-------------+
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI, Pydantic, Uvicorn |
| **Optimization** | PuLP (CBC), NumPy, SciPy |
| **Solar Physics** | pvlib, pandas, requests |
| **AI/ML** | Ollama (local LLMs), scikit-learn, Prophet |
| **Frontend** | React 18, TypeScript, Vite |
| **Visualization** | Plotly.js, Recharts, Leaflet |
| **Styling** | Tailwind CSS, Radix UI, Lucide icons |
| **State** | Zustand, React Query |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/optimize/run` | Run UC/ED optimization |
| `POST` | `/api/v1/optimize/run-with-solar` | UC/ED with auto solar forecast |
| `GET`  | `/api/v1/optimize/results/{job_id}` | Retrieve a stored optimization result |
| `GET`  | `/api/v1/optimize/status` | Solver config & availability |
| `GET`  | `/api/v1/forecast/solar` | Solar generation forecast (pvlib; `weather_source=clearsky\|pvgis_window`) |
| `GET`  | `/api/v1/forecast/load` | Statistical load forecast |
| `GET`  | `/api/v1/ai/load` | AI/LLM load forecast (synthetic input — see response `data_source`) |
| `POST` | `/api/v1/ai/load/custom` | AI load forecast from caller-supplied historical data |
| `GET`  | `/api/v1/pv/modules/search` | Search CEC PV module database |
| `GET`  | `/api/v1/pv/modules/{name}` | PV module detail |
| `GET`  | `/api/v1/weather/current` | Current weather data |
| `GET`  | `/api/v1/location/current` | Backend default location config |
| `GET`  | `/api/v1/generators/templates` | List built-in generator templates |
| `GET`  | `/api/v1/generators/presets/indonesia` | Indonesia market presets |
| `POST` | `/api/v1/generators/create` | Validate a custom generator definition |
| `GET`  | `/api/v1/marketplace/tariffs` | PLN tariff groups for bill→kWh conversion |
| `POST` | `/api/v1/marketplace/estimate` | Size a system + full financing/CO₂ analysis |
| `GET`  | `/api/v1/marketplace/installers` | Browse/filter installer partners |
| `GET`  | `/api/v1/marketplace/financiers` | Browse/filter financing products |
| `POST` | `/api/v1/marketplace/match` | Match a sized project to installers + financiers |
| `POST` | `/api/v1/marketplace/quote-request` | Submit a customer lead (per-IP rate-limited, validated) |
| `GET`  | `/api/v1/marketplace/portfolio` | Aggregated pipeline stats (capacity, CO₂, I-REC) |
| `GET`  | `/api/v1/marketplace/carbon/credits` | Standalone I-REC / avoided-CO₂ / revenue estimate |
| `GET`  | `/api/v1/marketplace/admin/leads` | List captured leads (token-gated via `LEADS_ADMIN_TOKEN`) |
| `GET`  | `/api/v1/marketplace/admin/leads/export` | Export leads (token-gated) |
| `GET`  | `/api/v1/market/rates` | Current USD/IDR + carbon price (live or fallback, with timestamp) |
| `POST` | `/api/v1/market/rates/refresh` | Force a live rates refetch |
| `GET`  | `/api/v1/health` | Lightweight health check (drives the frontend offline banner) |

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Ollama (optional, for AI forecasting)

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev        # Vite dev server on :3000 (configured in vite.config.ts)
```

### Ollama (optional)
```bash
ollama pull qwen3.5        # Or any local model
ollama serve               # Must be running for AI features
```

---

## Configuration

Environment variables in `backend/.env`:

```env
# Location
LATITUDE=-6.9147
LONGITUDE=107.6098
ALTITUDE=768
TIMEZONE=Asia/Jakarta

# Market (fallbacks when live rates are unavailable)
CURRENCY=IDR
USD_IDR_RATE=15500
CARBON_PRICE=50000            # Rp/tCO2
ENABLE_LIVE_RATES=true        # live USD/IDR + carbon price, TTL-cached
IREC_PRICE_USD=1.5            # indicative I-REC unit price

# Weather
ENABLE_PVGIS=true             # real ERA5 TMY per site, clear-sky fallback

# Marketplace
LEADS_ADMIN_TOKEN=            # set to enable /marketplace/admin/leads*

# Solver
SOLVER_NAME=cbc
```

---

## Project Structure

```
solara-optima-platform/
├── backend/
│   ├── app/
│   │   ├── api/               # REST endpoints (optimize, forecast, marketplace, market, pv_modules, ai, weather, location, generators)
│   │   ├── core/              # Config, logging, security
│   │   ├── models/            # Pydantic schemas (+ marketplace_schemas)
│   │   ├── services/          # optimizer, solar_forecast, finance, market_rates, carbon_credits, weather_pvgis, leads_store, pv_module_db, ai_forecast
│   │   └── main.py            # FastAPI app factory
│   ├── data/
│   │   ├── cec_modules_cache.json           # 21,677 CEC module specs (NREL SAM)
│   │   ├── pln_tariffs.json                 # PLN tariff groups
│   │   ├── installers.json, financiers.json # sample partners (labeled, with provenance)
│   │   ├── generator_templates.json         # editable generator presets
│   │   ├── load_profiles/     # Sample daily profiles
│   │   └── weather/           # TMY data files
│   ├── test_api.py, test_marketplace.py, test_marketplace_api.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/             # Dashboard, Optimization, SolarForecast, Generators, Marketplace, Settings
│   │   ├── components/        # Layout, LocationMap, ErrorBoundary, LazyPlot
│   │   ├── store/             # fleet (shared generator fleet store)
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
├── docs/
│   ├── DEMO.md                # demo script, cities, scenarios
│   ├── MARKETPLACE.md         # feature + CIIC form field mapping
│   ├── ROADMAP.md             # prioritized next steps
│   └── screenshot-dashboard.png
├── PROJECT_STATUS.md          # current status, verification log, commit history
├── docker-compose.yml
├── LICENSE
└── README.md
```

---

## Screenshots

### Dashboard
![Dashboard](docs/screenshot-dashboard.png)

### Solar Forecast with PV Module Selection
Browse 21,677 CEC modules, filter by manufacturer/technology, and auto-scale plant capacity.

### Optimization with Hourly Load Editor
24-cell editable load profile with live kWh totals and interactive Plotly charting.

---

## Recent Updates

| Date | Change |
|------|--------|
| **Jul 2026** | **Solar Aggregation & Financing Marketplace** — bill→system sizing, bankability (payback/IRR/NPV/LCOE), cash/loan/PPA, installer+financier matching, leads, portfolio |
| **Jul 2026** | **Carbon-credit (I-REC) module** — per-quote + portfolio certificates, avoided tCO₂, indicative revenue; `/marketplace/carbon/credits` endpoint |
| **Jul 2026** | **Real PVGIS (ERA5) irradiance** — per-site TMY for marketplace yield and `/forecast` (`pvgis_window`), disk-cached, clear-sky fallback |
| **Jul 2026** | **Live market rates** — USD/IDR + carbon price at startup + manual refresh, TTL cache, offline fallback |
| **Jul 2026** | Shared fleet store — Generators page fleet drives the Optimization dispatch and per-generator chart series |
| **Jul 2026** | Auto solar forecast anchored to local midnight (fixes ~7h shift: solar peaking at night) |
| **Jul 2026** | PV module manufacturer dropdown populated from the live CEC DB (21,677 modules) |
| **Jul 2026** | Bundle split: ~446 KB initial (was 5.2 MB) via lazy routes + on-demand Plotly; error boundary + backend-offline banner |
| **Jul 2026** | Leads store hardened — atomic append, per-IP rate limit, validation, token-gated admin endpoints |
| **May 2026** | Compose healthchecks across all services; ordered startup via `service_healthy` |
| **May 2026** | Generator templates extracted to `backend/data/generator_templates.json` (editable without code) |
| **May 2026** | Synthetic-input AI endpoints now flagged with `data_source: "synthetic"` |
| **May 2026** | Magic-number constants documented (CBC MIP gap, tropical tilt formula citations) |
| **May 2026** | CORS restricted to `CORS_ORIGINS` allowlist; `DEBUG=false` default |
| **May 2026** | Compose secrets moved to `.env` (no plaintext defaults); db port no longer host-exposed |
| **May 2026** | CEC modules CSV download hardened (`SHA256` verify, 50 MB cap, min-row sanity) |
| **May 2026** | Bounded LRU + 24h TTL on optimization result store (memory-leak fix) |
| **May 2026** | Frontend API URLs unified via `utils/api.ts` + `VITE_API_URL` (no more hardcoded `localhost:8000`) |
| **May 2026** | CI fail-loud: removed `\|\| echo` patterns; Trivy scan now blocks on HIGH/CRITICAL |
| **Apr 2026** | PV Module Database: CEC search + filter + manual entry + auto-scaling |
| **Apr 2026** | Auto geolocation: browser GPS → Nominatim → backend fallback |
| **Apr 2026** | Hourly load profile editor with live stats on Optimization page |
| **Apr 2026** | BESS binary charge/discharge mode fix, SOC constraint scaling |
| **Apr 2026** | Solar forecast unit fixes (kW/kWh consistency, no double divide-by-1000) |
| **Apr 2026** | Altitude override param added to forecast API |
| **Apr 2026** | Frontend presentation-mode typography and sidebar sizing |
| Apr 2026 | Location map + geocoding integration |
| Apr 2026 | Blue-themed dashboard UI |
| v1.0.0 | Initial release — UC/ED MILP, pvlib forecasting, Ollama AI |

---

## License

MIT License — see [LICENSE](./LICENSE)

## Author

**Zulfikar Aji Kusworo**  
GitHub: [@zakusworo](https://github.com/zakusworo)  
Email: greataji13@gmail.com  
DOI: [10.5281/zenodo.19653510](https://doi.org/10.5281/zenodo.19653510)
