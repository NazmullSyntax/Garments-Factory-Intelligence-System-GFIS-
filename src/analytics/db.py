"""
Shared DuckDB connection helper for analytics.

All KPI modules import get_connection() from here so we have one
place to configure the DB path and mode.
"""
from __future__ import annotations

from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "gfis.duckdb"


def get_connection(read_only: bool = True) -> duckdb.DuckDBPyConnection:
    """Open a connection to data/gfis.duckdb. Read-only by default."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"DuckDB file not found at {DB_PATH}. "
            "Run: python -m src.ingestion.load_to_duckdb"
        )
    return duckdb.connect(str(DB_PATH), read_only=read_only)