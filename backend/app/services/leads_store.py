"""
Append-only JSONL lead store + a best-effort per-client rate limiter.

This is the pragmatic pre-DB persistence layer for marketplace leads (see
ROADMAP §7 for the Postgres + auth migration). It hardens the naive
`open(..., "a")` approach with:
  - a threading lock so concurrent requests within one process never interleave
    lines (POSIX append of a single small write is already near-atomic, but the
    lock makes it deterministic and lets us fsync safely);
  - fsync so leads survive a crash immediately after the response is sent;
  - tolerant read/parse that skips corrupt lines instead of aborting portfolio
    stats.

It is intentionally process-local: behind a multi-worker deployment the JSONL
store should be replaced by the planned database.
"""

import json
import os
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from app.core.config import settings


class RateLimiter:
    """In-memory sliding-window per-key limiter (best-effort, single process)."""

    def __init__(self, max_per_minute: int):
        self.max = max(1, max_per_minute)
        self._hits: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            window = [t for t in self._hits.get(key, []) if now - t < 60.0]
            if len(window) >= self.max:
                self._hits[key] = window
                return False
            window.append(now)
            self._hits[key] = window
            return True


class LeadsStore:
    """Thread-safe append-only JSONL store with tolerant read/stats."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def append(self, lead: Dict) -> None:
        """Append one lead as a single JSON line; never raises to the caller."""
        line = json.dumps(lead, ensure_ascii=False) + "\n"
        with self._lock:
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as fh:
                    fh.write(line)
                    fh.flush()
                    try:
                        os.fsync(fh.fileno())
                    except OSError:  # pragma: no cover - fsync may be no-op on some FS
                        pass
            except OSError as e:  # pragma: no cover - non-fatal
                logger.error(f"Could not persist lead to {self.path}: {e}")

    def all(self) -> List[Dict]:
        """Return all parsed leads; corrupt lines are skipped, never raised."""
        if not self.path.exists():
            return []
        with self._lock:
            try:
                text = self.path.read_text(encoding="utf-8")
            except OSError as e:  # pragma: no cover - non-fatal
                logger.error(f"Could not read leads from {self.path}: {e}")
                return []
        leads: List[Dict] = []
        for raw in text.splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                leads.append(json.loads(raw))
            except json.JSONDecodeError:
                logger.warning("Skipped malformed lead line in store")
                continue
        return leads

    def stats(self) -> Dict:
        """Aggregated pipeline stats across all leads."""
        leads = self.all()
        total_capacity = sum(l.get("capacity_kwp") or 0.0 for l in leads)
        total_bill = sum(l.get("monthly_bill_idr") or 0.0 for l in leads)
        return {
            "total_leads": len(leads),
            "total_capacity_kwp": round(total_capacity, 1),
            "aggregated_monthly_bill_idr": round(total_bill),
        }


# Singletons shared by the API layer.
leads_store = LeadsStore(settings.DATA_DIR / "leads.jsonl")
quote_rate_limiter = RateLimiter(settings.LEADS_RATE_LIMIT_PER_MIN)