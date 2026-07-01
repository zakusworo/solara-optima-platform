# Solara Optima — Demo Guide & Script

A step-by-step walkthrough for demoing the platform end-to-end, with ready-made
scenarios and a list of demo cities. The **Solar Marketplace** is the hero flow
(the CIIC "Energy Transition" story); the other pages provide the technical depth.

> Numbers below are produced by the engine with the default **Bandung** location
> (specific yield ≈ 1,406 kWh/kWp/yr). They are illustrative, not a guarantee.

---

## 0. Launch (both servers must run)

```bash
# Terminal 1 — backend API (serves all /api/* calls)
cd solara-optima-platform/backend && source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd solara-optima-platform/frontend && npm run dev
```

Open **http://localhost:3000**. If a port is busy: `kill $(lsof -t -iTCP:8000 -sTCP:LISTEN)`.

Quick health check: `curl localhost:8000/health` → `{"status":"ok",...}`.

---

## 1. Demo cities

Pick a city, set it on the **Settings** page (map or "Search Place"), and choose the
matching **Province** in the Marketplace. Provinces are chosen so installer matching
returns partners (all are covered by at least one installer in `data/installers.json`).

| City | Province (Marketplace dropdown) | Lat | Lon | Persona to pitch |
|------|-------------------------------|-----|-----|------------------|
| **Jakarta** | DKI Jakarta | -6.2088 | 106.8456 | Office tower / mall / SME |
| **Bandung** *(default)* | Jawa Barat | -6.9147 | 107.6098 | Campus, textile SME |
| **Surabaya** | Jawa Timur | -7.2575 | 112.7521 | Factory / manufacturing |
| **Semarang** | Jawa Tengah | -6.9667 | 110.4167 | Port / industrial estate |
| **Yogyakarta** | DI Yogyakarta | -7.7956 | 110.3695 | Hotel / university |
| **Denpasar (Bali)** | Bali | -8.6705 | 115.2126 | Resort / hospitality |
| **Mataram** | Nusa Tenggara Barat | -8.5833 | 116.1167 | Island hotel / off-grid |
| **Medan** | Sumatera Utara | 3.5952 | 98.6722 | Palm-oil mill / industry |
| **Pekanbaru** | Riau | 0.5071 | 101.4478 | Industry |
| **Padang** | Sumatera Barat | -0.9471 | 100.4172 | Commercial |
| **Makassar** | Sulawesi Selatan | -5.1477 | 119.4327 | Commercial / industrial |
| **Marrakesh** 🌍 | *(int'l — nationwide installers)* | 31.6295 | -7.9811 | High-irradiance MENA site; northern-hemisphere check |

*International demo note:* Marrakesh (Morocco) is a high-solar-resource site useful for
showing the pvlib model outside Indonesia. Set its lat/lon on **Settings**; the yield
and forecast recompute for that location. It's northern-hemisphere, so optimal azimuth
flips to ~180° (south-facing) — the app shows this on the Settings panel. In the
Marketplace, leave **Province** as *Any / nationwide* (the sample installers are
Indonesia-based); PLN tariffs won't reflect Morocco, so treat the financing figures as
illustrative for international sites.

*Tip:* setting the location in **Settings** updates the backend default, so the
solar yield used by the Marketplace and Solar Forecast reflects that city. Yields
across Java/Bali are similar (~1,350–1,500 kWh/kWp/yr).

---

## 2. Ready-made scenarios (exact inputs → expected output)

Enter these on the **Solar Marketplace** page. Numbers are what the app will show.

### A. SME retail — Jakarta  ⭐ best headline demo
- Input mode **From my bill** · Monthly bill **25,000,000** · Tariff **Business 6,600 VA–200 kVA** · Segment **Commercial / SME** · Province **DKI Jakarta** · Roof **800 m²**
- **Output:** 114.3 kWp (208 panels, roof-capped) · CAPEX Rp 1.31 M(ilyar) · saving **Rp 174 jt/yr** · **payback 7.5 yr · IRR 14%** · bankability **72/100** · **137 tCO₂/yr**
- Financing: Cash 7.5 yr payback / Rp 4.29 B 25-yr net · Loan Rp 20.6 jt/mo · PPA Rp 0 down, Rp 12.3 jt/mo

### B. Factory — Surabaya (industrial scale)
- **From target size** · **500** kWp · Tariff **Industry >200 kVA (MV)** · Segment **Industrial** · Province **Jawa Timur** · Roof blank
- **Output:** 500 kWp · CAPEX Rp 5.75 B · saving **Rp 666 jt/yr** · **payback 8.5 yr · IRR 12.1%** · bankability 72 · **598 tCO₂/yr** (14,077 t / 25 yr)
- Good for the **PPA** pitch: Rp 0 upfront, Rp 47 jt/mo, still Rp 9.3 B lifetime net.

### C. Household — Bali (honest "marginal" case)
- **From my bill** · **3,500,000** · Tariff **Household 3,500–5,500 VA** · Segment **Residential** · Province **Bali** · Roof **60 m²**
- **Output:** 8.6 kWp · payback **11.2 yr · IRR 8.5% · NPV negative** · bankability **50/100** · 10 tCO₂/yr
- **Talking point:** the tool is honest — residential self-consumption is low and PLN
  no longer credits export, so cash payback is long. It steers this customer to a
  **PPA / low-rate KUR loan** rather than an oversized cash system.

### D. Hotel — Denpasar
- **From target size** · **200** kWp · Tariff **Business >200 kVA (MV)** · Segment **Commercial** · Province **Bali**
- **Output:** 200 kWp · CAPEX Rp 2.3 B · saving **Rp 235 jt/yr** · **payback 9.6 yr · IRR 10.4%** · 239 tCO₂/yr

---

## 3. Full walkthrough (≈5 minutes)

1. **Dashboard** — open http://localhost:3000. Show the location banner and the
   *Solar Resource Assessment* cards (irradiation, optimal tilt/azimuth). One line:
   *"This is the physics layer — a real pvlib solar model for Indonesia."*

2. **Settings → Location** — search or click the map to set your demo city (e.g.
   Surabaya). Confirm lat/lon + hemisphere update. *"Everything re-computes for the
   selected site."* (Optionally show Market Parameters: IDR, USD/IDR, carbon price.)

3. **Solar Marketplace** — the hero. Run **Scenario A**:
   - Toggle **From my bill**, type the bill, pick tariff/segment/province/roof → **Get Solar Estimate**.
   - Walk the **5 KPI cards** (size, saving, payback, 25-yr net, CO₂) and the
     **bankability bar**.
   - Show the **financing table** (Cash vs Green Loan vs Zero-CapEx PPA) — *"same
     system, three ways to pay; the PPA needs no capital."*
   - Point at the **cumulative-cashflow chart** crossing zero at the payback year.
   - Scroll to **Matched installers** and **Matched financing** — *"we're a neutral
     marketplace; we route the qualified project to partners."*
   - Click **Request quotes**, fill name/email → get a **lead reference**. *"That lead
     is captured; the Portfolio view aggregates many rooftops into one investable pipeline."*

4. **Solar Forecast** — show hourly pvlib generation for the site; browse the
   **10,000-module CEC database**, pick a panel, regenerate. *"The savings numbers
   are grounded in this physics, not a flat assumption."*

5. **Generators + Optimization** *(optional, for the technical/C&I + islands story)* —
   load the **Indonesia presets** (e.g. small-island diesel+solar), run the MILP
   dispatch, show cost and CO₂. *"For larger C&I and island grids, the same platform
   optimizes solar+battery dispatch against diesel — more avoided emissions."*

6. **Close on impact** — Scenario A alone avoids ~137 tCO₂/yr; a pipeline of 1,000
   such rooftops ≈ **130,000 tCO₂/yr**, and the basis for carbon-credit issuance.

---

## 4. CIIC talking points
- **Problem:** upfront cost + payback uncertainty block rooftop-solar adoption.
- **Solution:** instant, physics-grounded, *bankable* estimate + integrated financing + neutral installer marketplace.
- **Impact:** quantified tCO₂ per site, aggregated into a portfolio → carbon-credit ready.
- **Business model:** installer lead/referral fee, financier arrangement fee, SaaS/analytics; PPA needs no customer CapEx.
- **Depth/moat:** real pvlib engine + UC/ED dispatch optimizer underneath (not just a calculator).

See [`MARKETPLACE.md`](MARKETPLACE.md) for the field-by-field CIIC form mapping.

---

## 5. Tips & reset
- Nothing to reset between runs — each estimate is stateless. Submitted leads append to
  `backend/data/leads.jsonl`; delete that file to clear the Portfolio.
- If the sidebar/pages load but data is blank, the **backend isn't running** (start it on :8000).
- Change assumptions (CAPEX, yield, tariffs, grid factor) in `backend/app/services/finance.py`
  and `backend/data/*.json` — no code changes needed for the JSON data.
