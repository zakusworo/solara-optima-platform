"""
PVGIS (JRC) typical-meteorological-year irradiance fetcher.

PVGIS is free and needs no API key. We pull a TMY for a given lat/lon and turn
it into a pvlib-ready hourly DataFrame (ghi / dni / dhi / temp_air / wind_speed)
so the marketplace yield calc can use *real, cloud-adjusted* irradiance instead
of a clear-sky model. Results are disk-cached per location (TMY is stable) with
a configurable TTL, and every failure falls back to None so the caller can drop
to clear-sky — this never blocks or crashes an estimate.

Endpoint: {PVGIS_BASE_URL}/tmy?lat=..&lon=..&outputformat=json&raddatabase=..
TMY hourly fields used:
  G(h)  -> ghi   (global horizontal irradiance, W/m2)
  Gb(n) -> dni   (beam normal / direct, W/m2)
  Gd(h) -> dhi   (diffuse horizontal, W/m2)
  T2m   -> temp_air (deg C)
  WS10m -> wind_speed (m/s)
PVGIS TMY timestamps are UTC; we keep them tz-aware UTC so pvlib's solar-position
calculation (which works off the absolute instant + lat/lon) is correct.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests
from loguru import logger

from app.core.config import settings

# PVGIS radiation database. ERA5 (global reanalysis) reliably covers all of
# Indonesia; the satellite databases (SARAH2) do not cover this region on the
# current PVGIS instance, and NSRDB is Americas-only. ERA5 it is.
_RADDATABASES = ["PVGIS-ERA5"]

# In-process cache so repeated estimates for the same site don't re-read disk.
_MEM_CACHE: Dict[Tuple[float, float], pd.DataFrame] = {}


def _cache_path(latitude: float, longitude: float) -> Path:
    safe = settings.WEATHER_DIR / f"pvgis_{latitude:.4f}_{longitude:.4f}.json"
    return safe


def _is_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    age_s = time.time() - path.stat().st_mtime
    return age_s < settings.PVGIS_TTL_DAYS * 86400


def _parse_hourly(hourly: List[Dict]) -> Optional[pd.DataFrame]:
    """Convert PVGIS hourly records into a pvlib-ready DataFrame."""
    if not hourly:
        return None
    rows = []
    for rec in hourly:
        # PVGIS labels the timestamp key "time" or "time(UTC)"; find it robustly.
        tval = None
        for k, v in rec.items():
            if "time" in k.lower():
                tval = v
                break
        if tval is None:
            continue
        try:
            ts = pd.to_datetime(str(tval), format="%Y%m%d:%H%M", utc=True, errors="raise")
        except (ValueError, TypeError):
            # Some PVGIS responses use "YYYYMMDD:HH:MM" — try a flexible parse.
            try:
                ts = pd.to_datetime(str(tval).replace(":", "", 1), utc=True, errors="raise")
            except Exception:
                continue
        rows.append(
            {
                "ts": ts,
                "ghi": rec.get("G(h)", 0.0),
                "dni": rec.get("Gb(n)", 0.0),
                "dhi": rec.get("Gd(h)", 0.0),
                "temp_air": rec.get("T2m", 25.0),
                "wind_speed": rec.get("WS10m", 2.0),
            }
        )
    if not rows:
        return None
    df = pd.DataFrame(rows).set_index("ts").sort_index()
    # Numeric coercion + fill (defensive against nulls in the source).
    for col in ("ghi", "dni", "dhi", "temp_air", "wind_speed"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df


def _fetch(latitude: float, longitude: float) -> Optional[pd.DataFrame]:
    """Hit PVGIS, trying each raddatabase in order; return DataFrame or None."""
    params_base = {
        "lat": latitude,
        "lon": longitude,
        "outputformat": "json",
    }
    for db in _RADDATABASES:
        url = f"{settings.PVGIS_BASE_URL}/tmy"
        params = {**params_base, "raddatabase": db}
        try:
            resp = requests.get(url, params=params, timeout=settings.PVGIS_TIMEOUT_S)
            if resp.status_code != 200:
                logger.debug(f"PVGIS {db} returned {resp.status_code} for ({latitude},{longitude})")
                continue
            data = resp.json()
            outputs = data.get("outputs") or {}
            # `tmy` endpoint uses "tmy_hourly"; `seriescalc` uses "hourly".
            hourly = outputs.get("tmy_hourly") or outputs.get("hourly") or []
            df = _parse_hourly(hourly)
            if df is None or df.empty:
                logger.debug(f"PVGIS {db} returned no usable hourly data")
                continue
            # Persist raw hourly + provenance so we can rebuild without re-fetching.
            cache = _cache_path(latitude, longitude)
            cache.write_text(
                json.dumps(
                    {
                        "source": "PVGIS",
                        "raddatabase": db,
                        "url": url,
                        "fetched_at": int(time.time()),
                        "hourly": hourly,
                    }
                ),
                encoding="utf-8",
            )
            logger.info(
                f"PVGIS TMY loaded ({db}, {len(df)} hours) for ({latitude},{longitude})"
            )
            return df
        except Exception as e:  # network/timeout/parse — try next db, then give up
            logger.debug(f"PVGIS {db} fetch failed for ({latitude},{longitude}): {e}")
            continue
    logger.warning(
        f"All PVGIS databases failed for ({latitude},{longitude}); will use clear-sky"
    )
    return None


def get_tmy(latitude: float, longitude: float) -> Optional[pd.DataFrame]:
    """Return a cached or freshly-fetched TMY DataFrame, or None on failure."""
    if not settings.ENABLE_PVGIS:
        return None
    key = (round(latitude, 4), round(longitude, 4))
    if key in _MEM_CACHE:
        return _MEM_CACHE[key]

    path = _cache_path(latitude, longitude)
    df: Optional[pd.DataFrame] = None
    if _is_fresh(path):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            df = _parse_hourly(raw.get("hourly", []))
            if df is not None:
                logger.debug(f"PVGIS TMY cache hit for ({latitude},{longitude})")
        except Exception as e:  # corrupt cache — refetch
            logger.debug(f"PVGIS cache unreadable ({e}); refetching")

    if df is None or df.empty:
        df = _fetch(latitude, longitude)

    if df is not None and not df.empty:
        _MEM_CACHE[key] = df
        return df
    return None


def warm_default_location() -> None:
    """Pre-fetch the configured default location's TMY at startup (best-effort)."""
    if not settings.ENABLE_PVGIS:
        return
    try:
        get_tmy(settings.LATITUDE, settings.LONGITUDE)
    except Exception as e:  # pragma: no cover - never let startup hooks crash
        logger.warning(f"PVGIS warm-up failed: {e}")