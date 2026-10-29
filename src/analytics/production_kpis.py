"""
GFIS Production KPIs.

All functions:
  - read from `production_daily` via DuckDB
  - accept optional filters (date range, line, shift, order, style)
  - return a dict of scalar values
  - raise no silent errors: if there is no data, they return None-ish values
    with the count field set to 0 so callers can guard.

Formulas documented in docs/kpi_definitions.md (added later this day).

⚠️ All underlying data is SYNTHETIC. See README.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.analytics.db import get_connection


@dataclass
class KpiFilter:
    date_from: Optional[str] = None   # 'YYYY-MM-DD'
    date_to: Optional[str] = None
    line_id: Optional[str] = None
    shift: Optional[str] = None
    order_id: Optional[str] = None
    style_id: Optional[str] = None

    def where_clause(self, date_col: str = "production_date") -> tuple[str, list]:
        """Build a WHERE clause + param list. Returns ('1=1', []) if no filters."""
        parts: list[str] = []
        params: list = []
        if self.date_from:
            parts.append(f"{date_col} >= ?")
            params.append(self.date_from)
        if self.date_to:
            parts.append(f"{date_col} <= ?")
            params.append(self.date_to)
        if self.line_id:
            parts.append("line_id = ?")
            params.append(self.line_id)
        if self.shift:
            parts.append("shift = ?")
            params.append(self.shift)
        if self.order_id:
            parts.append("order_id = ?")
            params.append(self.order_id)
        if self.style_id:
            parts.append("style_id = ?")
            params.append(self.style_id)
        where = " AND ".join(parts) if parts else "1=1"
        return where, params


# ---------- KPI 1: Target Achievement % ----------
def target_achievement_pct(f: Optional[KpiFilter] = None) -> dict:
    """
    target_achievement_pct = (Σ actual_qty / Σ planned_qty) × 100

    Returns:
        {
            'actual_qty': int,
            'planned_qty': int,
            'achievement_pct': float | None,
            'n_rows': int,
        }
    """
    f = f or KpiFilter()
    where, params = f.where_clause()

    con = get_connection()
    try:
        row = con.execute(f"""
            SELECT
                COALESCE(SUM(actual_qty), 0)  AS actual_qty,
                COALESCE(SUM(planned_qty), 0) AS planned_qty,
                COUNT(*)                      AS n_rows
            FROM production_daily
            WHERE {where}
        """, params).fetchone()
    finally:
        con.close()

    actual, planned, n = row
    pct = (actual / planned * 100.0) if planned > 0 else None
    return {
        "actual_qty": int(actual),
        "planned_qty": int(planned),
        "achievement_pct": round(pct, 2) if pct is not None else None,
        "n_rows": int(n),
    }


# ---------- KPI 2: Production Variance (pcs) ----------
def production_variance_pcs(f: Optional[KpiFilter] = None) -> dict:
    """
    variance_pcs = Σ actual_qty − Σ planned_qty

    Negative = shortfall. Positive = overproduction.
    """
    ta = target_achievement_pct(f)
    variance = ta["actual_qty"] - ta["planned_qty"]
    return {
        "actual_qty": ta["actual_qty"],
        "planned_qty": ta["planned_qty"],
        "variance_pcs": variance,
        "variance_sign": "under" if variance < 0 else ("over" if variance > 0 else "on_target"),
        "n_rows": ta["n_rows"],
    }


# ---------- KPI 3: Line Efficiency % (SAM-based) ----------
def line_efficiency_pct(f: Optional[KpiFilter] = None) -> dict:
    """
    efficiency_pct = (Σ good_qty × sam_per_unit) / (Σ manpower × worked_hours × 60) × 100

    Numerator   = standard minutes of work produced (good pieces only)
    Denominator = actual labor minutes spent
    """
    f = f or KpiFilter()
    where, params = f.where_clause()

    con = get_connection()
    try:
        row = con.execute(f"""
            SELECT
                COALESCE(SUM(good_qty * sam_per_unit), 0) AS std_minutes,
                COALESCE(SUM(manpower_used * worked_hours * 60), 0) AS actual_minutes,
                COUNT(*) AS n_rows
            FROM production_daily
            WHERE {where}
        """, params).fetchone()
    finally:
        con.close()

    std_min, actual_min, n = row
    eff = (std_min / actual_min * 100.0) if actual_min > 0 else None
    return {
        "std_minutes": round(float(std_min), 2),
        "actual_minutes": round(float(actual_min), 2),
        "efficiency_pct": round(eff, 2) if eff is not None else None,
        "n_rows": int(n),
    }


# ---------- KPI 4: Labor Productivity (pcs per worker-hour) ----------
def labor_productivity_pcs_per_hr(f: Optional[KpiFilter] = None) -> dict:
    """
    productivity = Σ good_qty / Σ (manpower_used × worked_hours)

    Uses good_qty, not actual_qty. Rejects should not inflate productivity.
    """
    f = f or KpiFilter()
    where, params = f.where_clause()

    con = get_connection()
    try:
        row = con.execute(f"""
            SELECT
                COALESCE(SUM(good_qty), 0) AS good_qty,
                COALESCE(SUM(manpower_used * worked_hours), 0) AS worker_hours,
                COUNT(*) AS n_rows
            FROM production_daily
            WHERE {where}
        """, params).fetchone()
    finally:
        con.close()

    good, wh, n = row
    prod = (good / wh) if wh > 0 else None
    return {
        "good_qty": int(good),
        "worker_hours": round(float(wh), 2),
        "productivity_pcs_per_hr": round(prod, 3) if prod is not None else None,
        "n_rows": int(n),
    }


# ---------- KPI 5: Overtime Rate % ----------
def overtime_rate_pct(f: Optional[KpiFilter] = None) -> dict:
    """
    overtime_rate_pct = Σ overtime_hours / Σ worked_hours × 100

    Denominator = regular worked_hours (generator stores OT separately).
    Guard: if overtime_hours has NULLs (older data), coerce to 0.
    """
    f = f or KpiFilter()
    where, params = f.where_clause()

    con = get_connection()
    try:
        row = con.execute(f"""
            SELECT
                COALESCE(SUM(overtime_hours), 0) AS ot_hours,
                COALESCE(SUM(worked_hours), 0)  AS worked_hours,
                COUNT(*) AS n_rows
            FROM production_daily
            WHERE {where}
        """, params).fetchone()
    finally:
        con.close()

    ot, wh, n = row
    rate = (float(ot) / float(wh) * 100.0) if wh > 0 else None
    return {
        "overtime_hours": round(float(ot), 2),
        "worked_hours": round(float(wh), 2),
        "overtime_rate_pct": round(rate, 2) if rate is not None else None,
        "n_rows": int(n),
    }


# ---------- Convenience: all 5 KPIs in one call ----------
def all_production_kpis(f: Optional[KpiFilter] = None) -> dict:
    """Compute all 5 production KPIs with the same filter."""
    return {
        "target_achievement": target_achievement_pct(f),
        "variance": production_variance_pcs(f),
        "efficiency": line_efficiency_pct(f),
        "productivity": labor_productivity_pcs_per_hr(f),
        "overtime": overtime_rate_pct(f),
    }