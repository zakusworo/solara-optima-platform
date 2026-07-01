# Solara Optima Platform — Project Status

FastAPI + pvlib + PuLP/CBC backend, React 18 + Vite + TypeScript frontend.
Track: rooftop-solar aggregation, financing marketplace, and solar-aware
unit-commitment / economic-dispatch optimization for Indonesia.

> All commits are by **Zulfikar Aji Kusworo &lt;greataji13@gmail.com&gt;** — single
> committer, no co-authors. Current default branch `main` mirrors `origin/main`.

---

## Current status (as of 2026-07-01)

**Submission target:** Climate Impact Innovations Challenge (CIIC) 2026, deadline
2026-07-08. The platform runs end-to-end and is demo-ready.

### Working end-to-end
- **Solar Marketplace & Financing** — PLN bill / target kWp → pvlib-grounded sizing,
  bankability (CAPEX/payback/IRR/NPV/LCOE), CO₂ avoided, financing menu (cash / green
  loan / zero-CapEx PPA), installer + financier matching, lead capture, portfolio
  aggregation. Real PVGIS irradiance per province; sample partners honestly labeled.
- **Live market parameters** — real-time USD/IDR + carbon price on startup and on
  demand, with offline fallback.
- **Carbon-credit (I-REC) module** — 1 I-REC/MWh × 0.95 eligibility, avoided CO₂ via
  Indonesia grid factor 0.85 kgCO₂/kWh; per-quote panel + portfolio aggregate +
  standalone `/carbon/credits` endpoint.
- **Unit Commitment & Economic Dispatch** — CBC MILP solver; the generator fleet
  configured on the **Generators** page now drives the dispatch run and dashboard
  (shared fleet store), with auto clear-sky solar forecast aligned to local time.
- **Solar Forecast** — pvlib clear-sky + real PVGIS TMY; PV module DB from NREL SAM CEC
  (21,677 real panels), manufacturer/technology dropdowns populated from the live DB.
- **Demo safety** — error boundary + offline banner.

### Recent CIIC push (July 2026) — substantive changes
- `9f30c0a` Marketplace + live market rates.
- `bbca64f` Workarounds for known limitations (PVGIS, province→yield, bundle split,
  leads, provenance).
- `023c750` Carbon-credit (I-REC) module, real PVGIS in `/forecast`, demo safety.
- `ce4d546` **Fix** — PV module manufacturer dropdown now uses real CEC manufacturers
  (dynamic from DB + case-insensitive filter + placeholder row dropped).
- `12a8ba4` **Fix** — shared fleet store drives optimization dispatch (preset/template
  buttons wired, editable fleet + solar/battery, Optimization sends the real fleet and
  renders per-generator chart series instead of hardcoded values).
- `e8c929b` **Fix** — auto solar forecast anchored to local midnight (was starting at
  `now()`, shifting solar ~7h → solar at night, zero at midday; now peaks at noon).

### Known gaps / not yet done
- **Settings persistence** — `Save` persists **location** only. USD/IDR + carbon price
  are live-fed (backend is source of truth), but solver / PV-default / override fields
  have no backend persistence endpoint and are local-only. Needs a `/settings` save
  endpoint to make them stick.
- **Marketplace partners** — installer/financier listings are sample data, not yet
  verified/contracted partners (labeled in the UI). Replace before go-live.
- **Carbon credits go-live** — needs a live I-REC unit-price feed and a real
  dMRV/registry integration; current figures are indicative.
- **Result store** — in-process `OrderedDict` (single worker); replace with Redis when
  scaling horizontally.

---

## How to run

```bash
# Backend (FastAPI + uvicorn, with live reload)
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload --port 8000      # health: GET /api/v1/health

# Frontend (Vite dev server on :3000, proxies /api → :8000)
cd frontend && npm run dev                      # open http://localhost:3000
```

Smoke test: `cd backend && python test_marketplace.py`.
Demo guide: [`docs/DEMO.md`](docs/DEMO.md). Marketplace spec: [`docs/MARKETPLACE.md`](docs/MARKETPLACE.md).
Roadmap: [`docs/ROADMAP.md`](docs/ROADMAP.md).

---

## Commit history

Reverse-chronological. All commits by Zulfikar Aji Kusworo.

| Date       | Commit   | Message |
|------------|----------|---------|
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
> `git log --pretty=format:'%ad | \`%h\` | %s' --date=format:'%Y-%m-%d'`