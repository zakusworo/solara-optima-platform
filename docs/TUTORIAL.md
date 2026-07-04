# Solara Optima Platform — Beginner's Tutorial

This guide walks you through the web app from the moment you start it until
you get your first optimization result. No programming knowledge needed —
every step happens in the browser, and each step tells you what you should
see before moving on.

**What the app does, in plain words:** you describe a small power system —
solar panels, a battery, and one or more fuel generators — plus how much
electricity you need each hour of the day. The app then calculates the
cheapest way to run everything: when to use solar, when to charge or
discharge the battery, and when to turn generators on or off.

---

## 1. Start the web app

> Not installed yet? Follow the install steps in `QUICKSTART.md` first
> (clone, backend `pip install`, frontend `npm install`). You only do that
> once.

Open two terminals in the project folder.

**Terminal 1 — the engine (backend):**

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Wait for the line: `Application startup complete.`

**Terminal 2 — the website (frontend):**

```bash
cd frontend
npm run dev
```

Wait for: `Local: http://localhost:3000/`

Now open **http://localhost:3000** in your browser. You should see the
**Dashboard** with a "System Ready" badge, a Solar Resource Assessment for
Bandung, and a monthly irradiance chart. If the panels show errors instead,
the backend isn't running — check Terminal 1.

## 2. Know your way around

The sidebar has six pages. You will use them in this order:

| Page | What it's for |
|---|---|
| **Dashboard** | Overview: solar resource at your location, quick links |
| **Settings** | Where your site is (city, coordinates) and market prices |
| **Solar Forecast** | Preview how much energy your solar panels would make |
| **Generators** | Build your equipment list: solar size, battery, generators |
| **Optimization** | Run the calculation and see the results |
| **Marketplace** | Bonus: rooftop solar cost estimate for your electricity bill |

## 3. Set your location (Settings)

1. Click **Settings** in the sidebar.
2. The app comes pre-configured for **Bandung, Indonesia**. If that's fine,
   skip to step 4.
3. To change it: type a city name in the location search box, pick a result,
   and the **Latitude**, **Longitude**, **Altitude** and timezone fill in
   automatically. Click **Save**.
4. Notice the **Optimal PV Tilt** and **Optimal PV Azimuth** hints — the app
   knows that in the southern hemisphere panels should face north (azimuth
   0°).

You can leave everything else (currency, solver) at its defaults: prices in
Indonesian Rupiah and the free CBC solver.

## 4. Configure the PV system (solar panels + battery)

Go to the **Generators** page. Despite the name, this page holds your whole
equipment list, including solar and battery. Find the **System
Configuration** fields:

| Field | Meaning | Good starter value |
|---|---|---|
| **Solar PV (kW)** | Total size of your solar array. 1 kW ≈ 2 large panels. | `100` |
| **Battery (kWh)** | How much energy the battery can store. | `50` |
| **Battery Power (kW)** | How fast the battery can charge/discharge. | `25` |

**Optional — preview your solar production first.** Open the
**Solar Forecast** page, set **PV Capacity (kW)** to the same number, and
click the forecast button. You'll see a curve that is zero at night, rises
after sunrise, and peaks around midday.

Expected for 100 kW in Bandung on a clear day: roughly **500–540 kWh** over
the day with a midday peak near **73 kW**. You can also browse real panel
models under **PV Module Selection** (by manufacturer or technology) — for a
first run the defaults are fine.

## 5. Configure the generators

Still on the **Generators** page. Your **Generator Fleet** list is what the
optimizer will schedule — it needs at least one generator, because solar
alone can't cover the night.

The easy way — use a ready-made setup:

1. Look at **Indonesian Market Presets** (typical PLN configurations, e.g.
   small island or industrial microgrids) or **Generator Templates**
   (Diesel, Natural Gas, Coal, Biomass, Biogas).
2. Click one to add it to your fleet.

Or click **Add Custom Generator** and fill in the fields:

| Field | Plain-language meaning |
|---|---|
| **Generator Name** | Any label, e.g. "Gas Turbine 1" |
| **Fuel Type** | Diesel, natural gas, coal, biomass, biogas |
| **Min / Max Output (kW)** | The range it can run at while on |
| **Ramp Rate** | How fast it can change output per hour |
| **Fuel Cost (Rp/kWh)** | What one kWh of its electricity costs |
| **Emissions** | CO₂ per kWh, used for the emissions total |

**One rule of thumb before you continue:** add up the **Max Output** of all
your generators. It must cover your highest evening demand *on its own*,
because the sun is down then and the battery only helps a little. For the
default load (peak 170 kW), make sure your fleet totals **at least ~180 kW**
— e.g. one gas turbine of 200 kW, or a 100 kW turbine plus an 80 kW diesel.

## 6. Run the optimization and read the results

1. Open the **Optimization** page. Under **System Configuration** you'll see
   the location, solver (CBC MILP), and the PV/battery values you set —
   they carry over from the Generators page automatically.
2. Check the **Hourly Load Editor (kW)** — 24 bars, one per hour, showing
   how much electricity you need. The default profile is a typical day:
   low at night, a morning rise, and an evening peak. Drag or type to edit,
   or keep the defaults.
3. Click **Run Optimization**.

After a moment (usually under a second) the results appear:

- **Status: Optimal** — this word matters. *Optimal* means the app found the
  cheapest possible plan.
- **Total Cost** — the full day's running cost. For the default setup expect
  roughly **Rp 3–4 million**.
- **Solve Time** — how long the math took.

Then three charts, hour by hour:

- **Generation Stack** — colored bars showing which generator produces how
  much, each hour. You should see generators throttle down around midday
  (solar takes over) and ramp up for the evening peak.
- **Solar Generation** — the solar curve; zero at night, peak near noon.
- **Battery Storage** — charging (usually midday, from cheap solar) and
  discharging (usually evening, to shave the expensive peak).

**Reading the story in the numbers:** the optimizer uses free solar whenever
it can, stores the midday surplus in the battery, releases it in the
evening, and only burns fuel for what's left. That's the whole point of
the platform — and you can now test "what if" scenarios: bigger battery?
More solar? Cheaper fuel? Change a number and run again.

### If the status says "Infeasible"

*Infeasible* means: with this equipment, the demand physically cannot be met
in some hour — usually the evening peak. Fix it by raising a generator's
**Max Output**, adding another generator, or lowering the evening bars in
the load editor. Then run again.

## 7. Bonus: what would rooftop solar cost me? (Marketplace)

1. Open the **Marketplace** page.
2. Enter a monthly PLN electricity bill — try **Rp 1,500,000** with the
   residential tariff — and click **Estimate**.

Expected result: a recommended system around **4.8 kWp**, investment of
about **Rp 72 million**, the yearly savings, payback time (≈ 7–8 years),
and three ways to pay (cash, green loan, or a zero-upfront-cost PPA), plus
matched installers and the CO₂ you'd avoid.

## 8. Quick fixes

| What you see | What it means | What to do |
|---|---|---|
| Every panel shows an error | The backend (Terminal 1) isn't running | Start it, then refresh the browser |
| "No generators in fleet" when you click Run | The optimizer has nothing to schedule | Add a generator on the **Generators** page (step 5) |
| Status: **Infeasible** | Equipment can't cover the demand peak | See the fix box in step 6 |
| Solar forecast is all zeros | Forecast window is at night | Use a 24 h horizon |
| Page won't load at :3000 | Frontend (Terminal 2) isn't running | Start it and wait for the "Local:" line |

---

*Tested end-to-end on Linux, Python 3.14, Node 22 — July 2026. For
installation, API examples, and Docker deployment, see `QUICKSTART.md`.*
