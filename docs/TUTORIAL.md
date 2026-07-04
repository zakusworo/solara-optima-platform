# Solara Optima Platform — Step-by-Step Tutorial

A complete walkthrough: from a fresh machine to a running platform with real
optimization results. Every step includes the expected output so you can
verify you are on track.

**What you will end up with**

- A FastAPI backend on `http://localhost:8000` (interactive API docs at `/docs`)
- A React dashboard on `http://localhost:3000`
- A solved Unit Commitment / Economic Dispatch optimization with solar + battery
- A marketplace estimate for a rooftop solar system (Indonesian market, IDR)

---

## 1. Prerequisites

| Requirement | Minimum version | Check with |
|---|---|---|
| Git | any recent | `git --version` |
| Python | 3.12+ | `python3 --version` |
| Node.js | 20+ | `node --version` |
| npm | 9+ | `npm --version` |

About 2 GB of free disk space is needed for dependencies.

> **Note:** PostgreSQL, Redis, and Ollama are **not** required for this
> tutorial. They are only used by the optional Docker deployment (Section 9).

## 2. Clone the repository

```bash
git clone https://github.com/zakusworo/solara-optima-platform
cd solara-optima-platform
```

Expected: the folder contains `backend/`, `frontend/`, `data/`, `docs/`,
`docker-compose.yml`, and `QUICKSTART.md`.

## 3. Set up the backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements-minimal.txt
cp .env.example .env
```

The install takes a few minutes (pvlib, pandas, numpy, PuLP with the bundled
CBC solver).

**Important — edit `.env` before starting.** The example file includes three
`POSTGRES_*` variables that are only used by Docker Compose. The app rejects
unknown variables, so comment them out:

```bash
sed -i 's/^POSTGRES_/# POSTGRES_/' .env
```

If you skip this you will see on startup:

```
pydantic_core._pydantic_core.ValidationError: 3 validation errors for Settings
POSTGRES_USER
  Extra inputs are not permitted ...
```

## 4. Set up the frontend

```bash
cd ../frontend
npm install
```

Expected: finishes with `added ~650 packages` and **0 vulnerabilities**.

## 5. Start both servers

Use two terminals (or run each in the background).

**Terminal 1 — backend:**

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Expected output ends with:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

**Terminal 2 — frontend:**

```bash
cd frontend
npm run dev
```

Expected output:

```
VITE ready in ~1s
➜  Local:   http://localhost:3000/
```

## 6. Verify everything is up

```bash
curl http://localhost:8000/health
```

Expected:

```json
{"status":"ok","services":{"api":"running","optimization":"ready","forecasting":"ready"}}
```

Then open **http://localhost:3000** in your browser — the Dashboard loads with
the Bandung location pre-configured (-6.9147°S, 107.6098°E, 768 m).
The interactive API reference lives at **http://localhost:8000/docs**.

## 7. Get your first results

### 7a. Run an optimization from the UI

1. Open **http://localhost:3000/optimize**.
2. The form is pre-filled with a 24-hour load profile, a generator fleet,
   100 kW of PV, and a 50 kWh / 25 kW battery.
3. Click **Run Optimization**.

Expected result: solver status **Optimal**, a total cost in IDR
(≈ Rp 3–4 million for the default scenario), and charts showing the generator
schedule, solar output, and battery charge/discharge over 24 hours.

### 7b. Run the same optimization from the command line

```bash
curl -X POST http://localhost:8000/api/v1/optimize/run-with-solar \
  -H "Content-Type: application/json" \
  -d '{
    "load_profile": [80,75,70,65,60,65,85,100,120,130,125,120,115,110,115,125,140,160,170,165,150,130,110,95],
    "generators": [{
      "generator_id": 1, "name": "Gas Turbine",
      "min_output": 20, "max_output": 200,
      "ramp_up": 100, "ramp_down": 100,
      "min_uptime": 2, "min_downtime": 2,
      "initial_status": 1, "initial_output": 50,
      "startup_cost": 500000, "shutdown_cost": 0,
      "no_load_cost": 50000, "fuel_cost": 800,
      "emissions_rate": 0.45
    }],
    "pv_system_capacity": 100,
    "bess_capacity": 50,
    "bess_power_rating": 25
  }'
```

Expected: HTTP 200 with `"status": "Optimal"`, `"total_cost"` ≈ 3,000,000 IDR,
and hour-by-hour `generator_schedules`, `solar_output`, and
`battery_operation` arrays. Solve time is well under a second.

> The generator must be able to cover the evening peak (170 in this profile)
> when solar is zero — that is why `max_output` is 200 here. A 100-unit
> generator makes this scenario infeasible.

### 7c. Get a solar forecast

```bash
curl "http://localhost:8000/api/v1/forecast/solar?capacity=100&hours=24&weather_source=clearsky"
```

Expected: 24 hourly generation values for a 100 kW system in Bandung. On a
clear-sky day this totals roughly 500–540 kWh with a midday peak around 73 kW.

### 7d. Get a rooftop solar estimate (Marketplace)

Open **http://localhost:3000/marketplace**, enter a monthly PLN bill
(e.g. Rp 1,500,000, residential tariff), and click **Estimate**.

Expected result for that input: a recommended system of ≈ **4.8 kWp**,
CAPEX ≈ **Rp 72 million**, yearly savings, payback period, IRR/NPV, three
financing options (cash / green loan / zero-CapEx PPA), CO₂ avoided, and a
list of matched installers.

## 8. Run the smoke tests

The backend ships three script-style smoke tests. Run them directly with
Python (not via pytest — they are scripts, not pytest suites):

```bash
cd backend
source venv/bin/activate
python test_api.py             # core: optimizer + solar forecast
python test_marketplace.py     # financial model invariants
python test_marketplace_api.py # marketplace API end-to-end
```

Expected — each exits 0 and prints its checks, e.g.:

```
✓ Optimization completed!
  Total cost: Rp 3,391,295
✓ Solar forecast generated
  Total generation: 535.1 kWh
  Peak power: 72.78 kW
...
All Marketplace API tests passed
```

## 9. Optional: full Docker deployment

The compose stack adds PostgreSQL, Redis, and Ollama (for the AI-forecast
endpoints).

```bash
# in backend/.env: set POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
# (uncomment the lines you commented out in step 3)
docker compose up --build -d
```

Same URLs as dev mode: frontend on :3000, backend on :8000.

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Backend crashes at startup with `ValidationError ... POSTGRES_USER Extra inputs are not permitted` | Docker-only variables left in `.env` | Comment out the `POSTGRES_*` lines (step 3) |
| `422 Unprocessable Entity` on `/optimize/run` | Generator payload missing `shutdown_cost` / `no_load_cost` | Include both fields on every generator |
| Solver returns `Infeasible` | Fleet cannot cover peak load when solar is zero | Raise `max_output`, add generators, or increase battery power |
| Port 8000 or 3000 already in use | Another process bound the port | `uvicorn ... --port 8001` / `npm run dev -- --port 3001` |
| UI loads but every panel shows errors | Backend not running | Start the backend first; the frontend proxies `/api/*` to :8000 |

---

*Tested end-to-end on Linux (Fedora), Python 3.14, Node 22 — July 2026.*
