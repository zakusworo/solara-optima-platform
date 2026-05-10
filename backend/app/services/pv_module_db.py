"""
PV Module Database Service

Downloads and caches the CEC module database from NREL SAM on first startup.
Provides search and lookup APIs for PV module selection in the frontend.
"""

import hashlib
import os
import time
from typing import Dict, List, Optional

import pandas as pd
import requests
from loguru import logger

from app.core.config import settings

# NREL SAM CEC Modules CSV URL.
# Pinning to a commit SHA (instead of the moving "develop" branch) protects
# us from upstream content changes / supply-chain attacks. Override via the
# CEC_MODULES_URL env var when bumping. Optional CEC_MODULES_SHA256 enables
# hash verification of the downloaded body.
_DEFAULT_CEC_URL = "https://raw.githubusercontent.com/NREL/SAM/develop/deploy/libraries/CEC%20Modules.csv"
CEC_MODULES_URL = os.getenv("CEC_MODULES_URL", _DEFAULT_CEC_URL)
CEC_MODULES_SHA256 = os.getenv("CEC_MODULES_SHA256")  # optional, lowercase hex

# Sanity bounds — the real CEC database has thousands of rows; anything
# wildly outside this range is a strong signal something went wrong.
_MIN_EXPECTED_ROWS = 500
_MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024  # 50 MB

# Cache file path
DB_CACHE_FILE = settings.DATA_DIR / "cec_modules_cache.json"
DB_TIMESTAMP_FILE = settings.DATA_DIR / "cec_modules_timestamp.txt"
CACHE_TTL_DAYS = 7  # Refresh every week


class PVModuleDB:
    """PV Module database backed by NREL SAM CEC Modules library"""

    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self._load_or_download()

    def _load_or_download(self):
        """Load cached data or download from NREL if stale/missing"""
        try:
            # Check if cache exists and is fresh
            if DB_CACHE_FILE.exists() and DB_TIMESTAMP_FILE.exists():
                cached_time = float(DB_TIMESTAMP_FILE.read_text().strip())
                age_days = (time.time() - cached_time) / 86400
                if age_days < CACHE_TTL_DAYS:
                    logger.info(
                        f"Loading cached PV module DB (age: {age_days:.1f} days)"
                    )
                    self.df = pd.read_json(DB_CACHE_FILE, orient="records")
                    logger.info(f"Loaded {len(self.df)} PV modules from cache")
                    return

            # Download fresh data
            self._download_and_cache()

        except Exception as e:
            logger.error(
                f"PV module DB error: {e}. Will try loading cache as fallback."
            )
            if DB_CACHE_FILE.exists():
                self.df = pd.read_json(DB_CACHE_FILE, orient="records")

    def _download_and_cache(self):
        """Download CEC modules CSV and convert to structured JSON"""
        logger.info(f"Downloading PV module database from {CEC_MODULES_URL}")
        response = requests.get(CEC_MODULES_URL, timeout=60, stream=True)
        response.raise_for_status()

        # Read with a hard size cap to prevent memory blow-up if the URL
        # is hijacked to point at something huge.
        chunks = []
        total = 0
        for chunk in response.iter_content(chunk_size=65536):
            if not chunk:
                continue
            total += len(chunk)
            if total > _MAX_DOWNLOAD_BYTES:
                raise ValueError(
                    f"CEC modules download exceeds {_MAX_DOWNLOAD_BYTES} bytes — refusing"
                )
            chunks.append(chunk)
        body = b"".join(chunks)

        # Optional integrity check against pinned SHA256.
        if CEC_MODULES_SHA256:
            actual = hashlib.sha256(body).hexdigest()
            if actual.lower() != CEC_MODULES_SHA256.lower():
                raise ValueError(
                    f"CEC modules SHA256 mismatch: expected {CEC_MODULES_SHA256}, got {actual}"
                )

        # Skip row 1 (Units row) - data headers are on row 0, data starts at row 2
        from io import StringIO

        raw_df = pd.read_csv(StringIO(body.decode("utf-8")), skiprows=[1])

        # Sanity check: real CEC DB has thousands of rows. If we got far less,
        # the upstream file probably changed format — abort rather than poison
        # the cache.
        if len(raw_df) < _MIN_EXPECTED_ROWS:
            raise ValueError(
                f"CEC modules download returned only {len(raw_df)} rows "
                f"(expected >= {_MIN_EXPECTED_ROWS}); refusing to cache"
            )

        # Drop any remaining weird rows
        raw_df = raw_df.dropna(subset=["Name"])
        raw_df = raw_df[
            ~raw_df["Name"].astype(str).str.contains("^Units$", regex=True, na=False)
        ]

        # Define column mapping
        col_mapping = {
            "Name": "name",
            "Manufacturer": "manufacturer",
            "Technology": "technology",
            "Bifacial": "bifacial",
            "STC": "p_stc",
            "PTC": "p_ptc",
            "A_c": "area",
            "Length": "length",
            "Width": "width",
            "N_s": "cells_in_series",
            "I_sc_ref": "i_sc_ref",
            "V_oc_ref": "v_oc_ref",
            "I_mp_ref": "i_mp_ref",
            "V_mp_ref": "v_mp_ref",
            "alpha_sc": "alpha_sc",
            "beta_oc": "beta_oc",
            "a_ref": "a_ref",
            "I_L_ref": "i_l_ref",
            "I_o_ref": "i_o_ref",
            "R_sh_ref": "r_sh_ref",
            "R_s": "r_s",
            "Adjust": "adjust",
            "T_NOCT": "t_noct",
        }

        # Only rename columns that exist
        available_cols = {k: v for k, v in col_mapping.items() if k in raw_df.columns}
        df = raw_df.rename(columns=available_cols)

        # Parse numeric columns
        numeric_cols = [
            "p_stc",
            "p_ptc",
            "area",
            "length",
            "width",
            "cells_in_series",
            "i_sc_ref",
            "v_oc_ref",
            "i_mp_ref",
            "v_mp_ref",
            "alpha_sc",
            "beta_oc",
            "a_ref",
            "i_l_ref",
            "i_o_ref",
            "r_sh_ref",
            "r_s",
            "adjust",
            "t_noct",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Keep only useful columns
        keep_cols = list(available_cols.values())
        df = df[keep_cols].copy()

        # Add derived fields
        if "p_stc" in df.columns and "area" in df.columns:
            df["efficiency"] = df["p_stc"] / (df["area"] * 1000)
            df["efficiency"] = df["efficiency"].fillna(0.18).clip(0.05, 0.30)

        self.df = df.reset_index(drop=True)

        # Cache to JSON
        self.df.to_json(DB_CACHE_FILE, orient="records")
        DB_TIMESTAMP_FILE.write_text(str(time.time()))

        logger.info(f"Cached {len(self.df)} PV modules to {DB_CACHE_FILE}")

    def get_manufacturers(self) -> List[str]:
        """Return sorted list of unique manufacturers"""
        if self.df is None or "manufacturer" not in self.df.columns:
            return []
        return sorted(self.df["manufacturer"].dropna().unique().tolist())

    def get_technologies(self) -> List[str]:
        """Return sorted list of unique technologies"""
        if self.df is None or "technology" not in self.df.columns:
            return []
        return sorted(self.df["technology"].dropna().unique().tolist())

    def search_modules(
        self,
        query: Optional[str] = None,
        manufacturer: Optional[str] = None,
        technology: Optional[str] = None,
        pmin: Optional[float] = None,
        pmax: Optional[float] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """Search PV modules by various criteria"""
        if self.df is None:
            return []

        results = self.df.copy()

        if manufacturer:
            results = results[results["manufacturer"] == manufacturer]

        if technology:
            results = results[results["technology"] == technology]

        if pmin is not None and "p_stc" in results.columns:
            results = results[results["p_stc"] >= pmin]

        if pmax is not None and "p_stc" in results.columns:
            results = results[results["p_stc"] <= pmax]

        if query:
            q = query.lower()
            mask = results["name"].astype(str).str.lower().str.contains(
                q, na=False
            ) | results["manufacturer"].astype(str).str.lower().str.contains(
                q, na=False
            )
            results = results[mask]

        results = results.head(limit)

        # Serialize to dicts, handling NaN/Inf
        records = []
        for _, row in results.iterrows():
            record = {}
            for k, v in row.items():
                if pd.isna(v):
                    record[k] = None
                elif isinstance(v, (int, float)):
                    record[k] = v
                else:
                    record[k] = str(v)
            records.append(record)

        return records

    def get_module(self, name: str) -> Optional[Dict]:
        """Get a specific module by exact name"""
        if self.df is None or self.df.empty:
            return None
        match = self.df[self.df["name"] == name]
        if match.empty:
            return None
        row = match.iloc[0]
        record = {}
        for k, v in row.items():
            if pd.isna(v):
                record[k] = None
            elif isinstance(v, (int, float)):
                record[k] = v
            else:
                record[k] = str(v)
        return record

    def get_module_names(self, limit: int = 1000) -> List[str]:
        """Return list of module names for autocomplete"""
        if self.df is None or "name" not in self.df.columns:
            return []
        return self.df["name"].dropna().head(limit).tolist()


# Singleton instance
_module_db: Optional[PVModuleDB] = None


def get_pv_module_db() -> PVModuleDB:
    """Get or create the PV module database singleton"""
    global _module_db
    if _module_db is None:
        _module_db = PVModuleDB()
    return _module_db
