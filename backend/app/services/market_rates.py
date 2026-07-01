"""
Live market-rates service.

Fetches the real-time USD/IDR exchange rate and (optionally) a carbon price at
startup and on demand, caches them in memory with a TTL, and falls back to the
configured defaults whenever a source is unavailable or offline. The refreshed
values are written back to `settings` so downstream consumers (e.g. the UC/ED
optimizer's carbon cost) use the live figures.
"""

import time
from datetime import datetime, timezone
from typing import Dict, Optional

import requests
from loguru import logger

from app.core.config import settings

_FETCH_TIMEOUT_S = 5


class MarketRatesService:
    """In-memory cache of live market rates with graceful fallback."""

    def __init__(self):
        self._usd_idr = {
            "value": settings.USD_IDR_RATE,
            "source": "config (default)",
            "is_live": False,
        }
        self._carbon = {
            "value": settings.CARBON_PRICE,
            "source": "config (default)",
            "is_live": False,
        }
        self._fetched_at: Optional[float] = None  # epoch seconds

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def get(self) -> Dict:
        """Return the current cached rates and their provenance."""
        return {
            "usd_idr": self._usd_idr["value"],
            "carbon_price": self._carbon["value"],
            "sources": {
                "usd_idr": self._usd_idr["source"],
                "carbon_price": self._carbon["source"],
            },
            "is_live": {
                "usd_idr": self._usd_idr["is_live"],
                "carbon_price": self._carbon["is_live"],
            },
            "fetched_at": (
                datetime.fromtimestamp(self._fetched_at, tz=timezone.utc).isoformat()
                if self._fetched_at
                else None
            ),
            "is_fresh": self.is_fresh(),
            "ttl_hours": settings.RATES_TTL_HOURS,
        }

    def is_fresh(self) -> bool:
        if not self._fetched_at:
            return False
        return (time.time() - self._fetched_at) < settings.RATES_TTL_HOURS * 3600

    def refresh(self) -> Dict:
        """Re-fetch all rates (synchronous; safe to run in a thread)."""
        if not settings.ENABLE_LIVE_RATES:
            logger.info("Live rates disabled (ENABLE_LIVE_RATES=false); using defaults")
            return self.get()

        self._refresh_usd_idr()
        self._refresh_carbon_price()
        self._fetched_at = time.time()

        # Propagate to settings so the optimizer/finance use live values.
        settings.USD_IDR_RATE = self._usd_idr["value"]
        settings.CARBON_PRICE = self._carbon["value"]
        return self.get()

    # ------------------------------------------------------------------ #
    # Providers
    # ------------------------------------------------------------------ #
    def _refresh_usd_idr(self) -> None:
        try:
            resp = requests.get(settings.FX_RATES_URL, timeout=_FETCH_TIMEOUT_S)
            resp.raise_for_status()
            data = resp.json()
            rate = (data.get("rates") or data.get("conversion_rates") or {}).get("IDR")
            if not rate:
                raise ValueError("IDR rate missing in FX response")
            self._usd_idr = {
                "value": round(float(rate), 2),
                "source": settings.FX_RATES_URL,
                "is_live": True,
            }
            logger.info(f"Live USD/IDR = {self._usd_idr['value']:,.2f}")
        except Exception as e:
            logger.warning(
                f"USD/IDR fetch failed ({e}); falling back to {settings.USD_IDR_RATE}"
            )
            self._usd_idr = {
                "value": settings.USD_IDR_RATE,
                "source": "config (fallback)",
                "is_live": False,
            }

    def _refresh_carbon_price(self) -> None:
        url = settings.CARBON_PRICE_URL
        if not url:
            # No free live IDR carbon feed configured — use the statutory/config value.
            self._carbon = {
                "value": settings.CARBON_PRICE,
                "source": "config (no live source)",
                "is_live": False,
            }
            return
        try:
            resp = requests.get(url, timeout=_FETCH_TIMEOUT_S)
            resp.raise_for_status()
            data = resp.json()
            price = data.get("price_idr_per_tco2") or data.get("price")
            if price is None:
                raise ValueError("carbon price missing in response")
            self._carbon = {
                "value": round(float(price), 2),
                "source": url,
                "is_live": True,
            }
            logger.info(f"Live carbon price = Rp {self._carbon['value']:,.0f}/tCO2")
        except Exception as e:
            logger.warning(
                f"Carbon price fetch failed ({e}); falling back to {settings.CARBON_PRICE}"
            )
            self._carbon = {
                "value": settings.CARBON_PRICE,
                "source": "config (fallback)",
                "is_live": False,
            }


# Global singleton
market_rates_service = MarketRatesService()
