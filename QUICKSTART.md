# Solar UC/ED Platform - Quick Start Guide

## Project Overview

A modern, production-grade **Unit Commitment & Economic Dispatch** optimization platform with:
- **Solar PV integration** using pvlib (Bandung-optimized)
- **Battery storage** modeling
- **MILP optimization** with PuLP
- **FastAPI backend** + **React frontend**
- **Indonesian market** presets (IDR pricing, PLN configurations)

## What's Been Built

### Backend (`/backend`)
- ✅ FastAPI application with REST API
- ✅ MILP optimizer (Unit Commitment + Economic Dispatch)
- ✅ Solar forecasting service (pvlib, southern hemisphere optimized)
- ✅ Battery energy storage modeling
- ✅ Generator fleet management with Indonesian presets
- ✅ Weather data integration

### Frontend (`/frontend`)
- ✅ React + TypeScript dashboard
- ✅ Interactive optimization interface
- ✅ Solar forecast visualization
- ✅ Generator configuration UI
- ✅ Settings management

### Key Features
1. **Southern Hemisphere Optimization**: Azimuth 0° (North-facing) for Indonesia
2. **Bandung Location**: Pre-configured (-6.9147°S, 107.6098°E, 768m)
3. **IDR Pricing**: Indonesian Rupiah market rates (~15,500 Rp/USD)
4. **PLN Presets**: Typical small island, industrial, rural microgrid configs

## Installation

### Option 1: Automated Setup
```bash
cd ~/projects/solar-uc-ed-platform
./setup.sh
```

### Option 2: Manual Setup

#### Backend
```bash
cd ~/projects/solar-uc-ed-platform/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-minimal.txt
cp .env.example .env
```

#### Frontend
```bash
cd ~/projects/solar-uc-ed-platform/frontend
npm install
```

## Running the Platform

### Terminal 1: Backend
```bash
cd ~/projects/solar-uc-ed-platform/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access API docs: **http://localhost:8000/docs**

### Terminal 2: Frontend
```bash
cd ~/projects/solar-uc-ed-platform/frontend
npm run dev
```

Access UI: **http://localhost:3000**

## API Endpoints

### Optimization
- `POST /api/v1/optimize/run` - Run UC/ED optimization
- `POST /api/v1/optimize/run-with-solar` - Run with auto solar forecast
- `GET /api/v1/optimize/results/{job_id}` - Get results
- `GET /api/v1/optimize/status` - Solver status

### Forecasting
- `GET /api/v1/forecast/solar` - Solar generation forecast
- `GET /api/v1/forecast/load` - Load forecast
- `GET /api/v1/forecast/compare` - Compare tilt scenarios

### Generators
- `GET /api/v1/generators/templates` - Generator templates
- `GET /api/v1/generators/presets/indonesia` - Indonesian market presets
- `POST /api/v1/generators/create` - Create custom generator

### Weather
- `GET /api/v1/weather/current` - Current weather
- `GET /api/v1/weather/forecast` - Weather forecast
- `GET /api/v1/weather/solar-resource` - Solar resource assessment

## Example: Run Optimization

```bash
curl -X POST http://localhost:8000/api/v1/optimize/run-with-solar \
  -H "Content-Type: application/json" \
  -d '{
    "load_profile": [80, 75, 70, 65, 60, 65, 85, 100, 120, 130, 125, 120, 115, 110, 115, 125, 140, 160, 170, 165, 150, 130, 110, 95],
    "generators": [
      {
        "generator_id": 1,
        "name": "Gas Turbine",
        "min_output": 10,
        "max_output": 100,
        "ramp_up": 50,
        "ramp_down": 50,
        "min_uptime": 2,
        "min_downtime": 2,
        "initial_status": 1,
        "initial_output": 50,
        "startup_cost": 500000,
        "fuel_cost": 800,
        "emissions_rate": 0.45
      }
    ],
    "pv_system_capacity": 100,
    "bess_capacity": 50,
    "bess_power_rating": 25
  }'
```

## Project Structure

```
solar-uc-ed-platform/
├── backend/
│   ├── app/
│   │   ├── api/              # REST endpoints
│   │   ├── core/             # Config, logging
│   │   ├── models/           # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   │   ├── optimizer.py  # MILP solver
│   │   │   └── solar_forecast.py  # pvlib integration
│   │   └── main.py           # FastAPI app
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Optimization.tsx
│   │   │   ├── SolarForecast.tsx
│   │   │   └── Generators.tsx
│   │   └── App.tsx
│   └── package.json
├── data/
│   ├── weather/
│   └── load_profiles/
├── docs/
├── setup.sh
└── README.md
```

## Configuration

### Location (Bandung Default)
```env
LATITUDE=-6.9147
LONGITUDE=107.6098
ALTITUDE=768
TIMEZONE=Asia/Jakarta
```

### Market
```env
CURRENCY=IDR
USD_IDR_RATE=15500
CARBON_PRICE=50000
```

### Optimization
```env
SOLVER_NAME=cbc
SOLVER_TIME_LIMIT=300
```

## Next Steps / Enhancements

### Pending Features
1. **AI Forecasting Agents** (Ollama integration)
   - Load forecasting with LLM
   - Solar prediction refinement
   
2. **Real-time Data APIs**
   - BMKG weather integration
   - Live electricity prices
   - CEC module database

3. **Advanced Visualizations**
   - Export to PDF/PPTX
   - Time-series comparisons
   - Scenario analysis

4. **Database Integration**
   - PostgreSQL for historical data
   - Redis caching
   - Celery task queues

### Save as Skill
Consider saving this project structure as a skill for future renewable energy projects:
- Multi-agent AI + physics engine architecture
- Southern hemisphere PV optimization
- Indonesian market configurations

## Author

**Zulfikar Aji Kusworo**  
Politeknik Energi dan Pertambangan Bandung  
Email: greataji13@gmail.com  
GitHub: zakusworo  
DOI: 10.5281/zenodo.19650332

## License

MIT License
