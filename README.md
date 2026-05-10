# Solara Optima Platform

**AI-Enhanced Unit Commitment & Economic Dispatch for Renewable-Integrated Power Systems**

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19653510.svg)](https://doi.org/10.5281/zenodo.19653510)

A modern platform for **Unit Commitment & Economic Dispatch (UC/ED)** optimization with deep integration of **solar PV forecasting**, **battery storage scheduling**, and **multi-agent AI forecasting**. Built specifically for Indonesian energy markets with real-time pvlib physics-based generation modeling and Ollama-powered LLM agents.

**Live Demo**: https://github.com/zakusworo/solara-optima-platform

---

## Highlights

- **MILP Solver** (PuLP) for mixed-integer optimal dispatch with generator constraints, ramp rates, min uptime/downtime
- **pvlib Integration** for physics-based solar generation forecasting using real meteorological data
- **PV Module Database** with 10,000+ CEC modules — search, filter, and auto-scale plant capacity by module selection
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
| **Weather Integration** | Real-time/past weather data via pvlib/pandas TMY data |
| **Hourly Resolution** | Up to 168h forecast horizon |

### PV Module Database

| Feature | Description |
|---------|-------------|
| **CEC Module Cache** | 10,000+ commercial PV modules cached locally from CEC/Sandia databases |
| **Search & Filter** | By manufacturer, technology (Mono/Multi/CdTe), power range, text search |
| **Module Selection** | Click-to-select from browsable table; auto-suggests plant capacity based on module wattage |
| **Manual Entry** | Override with custom STC/PTC, efficiency, Vmp, Imp, temperature coefficients |
| **Auto-Scaling** | Enter desired plant capacity (kW) — frontend calculates module count and total output |

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
| **Interactive Plotly Charts** | Generation forecasts, load profiles, dispatch schedules, temperature curves |
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
| `GET`  | `/api/v1/optimize/status` | Solver config & availability |
| `GET`  | `/api/v1/forecast/solar` | Solar generation forecast (pvlib) |
| `GET`  | `/api/v1/forecast/load` | Statistical load forecast |
| `GET`  | `/api/v1/ai/load` | AI/LLM load forecast |
| `GET`  | `/api/v1/pv/modules/search` | Search CEC PV module database |
| `GET`  | `/api/v1/pv/modules/{name}` | PV module detail |
| `GET`  | `/api/v1/weather/current` | Current weather data |
| `GET`  | `/api/v1/location/current` | Backend default location config |
| `POST` | `/api/v1/generators` | Manage generator fleet |

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
npm run dev        # Vite dev server on :5173
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
LATITUDE=-6.9147
LONGITUDE=107.6098
ALTITUDE=768
TIMEZONE=Asia/Jakarta
BASE_CURRENCY=IDR
USD_IDR_RATE=15500
CARBON_PRICE=50000
SOLVER_NAME=CBC
```

---

## Project Structure

```
solara-optima-platform/
├── backend/
│   ├── app/
│   │   ├── api/               # REST endpoints (optimize, forecast, pv_modules, ai, weather, location)
│   │   ├── core/              # Config, logging, security
│   │   ├── models/            # Pydantic schemas
│   │   ├── services/          # Optimizer, solar_forecast, pv_module_db, ai_forecast
│   │   └── main.py            # FastAPI app factory
│   ├── data/
│   │   ├── cec_modules_cache.json          # 10K+ CEC module specs
│   │   ├── cec_modules_timestamp.txt        # Cache freshness marker
│   │   ├── load_profiles/      # Sample daily profiles
│   │   └── weather/            # TMY data files
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/             # Dashboard, Optimization, SolarForecast, Generators, Settings
│   │   ├── components/        # Layout, LocationMap
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
├── docs/
│   └── screenshot-dashboard.png
├── docker-compose.yml
├── LICENSE
└── README.md
```

---

## Screenshots

### Dashboard
![Dashboard](docs/screenshot-dashboard.png)

### Solar Forecast with PV Module Selection
Browse 10,000+ CEC modules, filter by manufacturer/technology, and auto-scale plant capacity.

### Optimization with Hourly Load Editor
24-cell editable load profile with live kWh totals and interactive Plotly charting.

---

## Recent Updates

| Date | Change |
|------|--------|
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
Affiliation: Politeknik Energi dan Pertambangan Bandung, Indonesia  
DOI: [10.5281/zenodo.19653510](https://doi.org/10.5281/zenodo.19653510)
