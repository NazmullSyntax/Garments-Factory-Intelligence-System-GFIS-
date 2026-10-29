"""
KPI tests for production_kpis.py.

Strategy:
1. Pure arithmetic tests against known slices of the real (synthetic) data.
2. Hand-computed expected values using the same DuckDB query.
   If the function and the query disagree, we learn something.
3. Guard tests for empty slices.

These are NOT tautological: they call the function and then independently
recompute the expected answer from the raw table.
"""
from __future__ import annotations

import pytest

from src.analytics.db import get_connection
from src.analytics.production_kpis import (
    KpiFilter,
    all_production_kpis,
    labor_productivity_pcs_per_hr,
    line_efficiency_pct,
    overtime_rate_pct,
    production_variance_pcs,
    target_achievement_pct,
)


# ---------- KPI 1: Target Achievement ----------
def test_target_achievement_all_data():
    result = target_achievement_pct()

    con = get_connection()
    try:
        actual, planned = con.execute("""
            SELECT SUM(actual_qty), SUM(planned_qty) FROM production_daily
        """).fetchone()
    finally:
        con.close()

    assert result["actual_qty"] == actual
    assert result["planned_qty"] == planned
    expected_pct = round(actual / planned * 100.0, 2)
    assert result["achievement_pct"] == expected_pct


def test_target_achievement_empty_filter_returns_none_pct():
    result = target_achievement_pct(KpiFilter(line_id="LN-99"))
    assert result["n_rows"] == 0
    assert result["achievement_pct"] is None
    assert result["actual_qty"] == 0


def test_target_achievement_pct_in_valid_range():
    """On the real synthetic data, overall achievement must be plausible."""
    result = target_achievement_pct()
    assert result["achievement_pct"] is not None
    assert 70.0 <= result["achievement_pct"] <= 120.0, (
        f"achievement {result['achievement_pct']} % is outside a plausible range"
    )


# ---------- KPI 2: Variance ----------
def test_variance_equals_actual_minus_planned():
    ta = target_achievement_pct()
    v = production_variance_pcs()
    assert v["variance_pcs"] == ta["actual_qty"] - ta["planned_qty"]
    assert v["variance_pcs"] == v["actual_qty"] - v["planned_qty"]


def test_variance_sign_label():
    v = production_variance_pcs()
    if v["variance_pcs"] < 0:
        assert v["variance_sign"] == "under"
    elif v["variance_pcs"] > 0:
        assert v["variance_sign"] == "over"
    else:
        assert v["variance_sign"] == "on_target"


# ---------- KPI 3: Efficiency ----------
def test_efficiency_matches_independent_query():
    result = line_efficiency_pct()

    con = get_connection()
    try:
        std_min, actual_min = con.execute("""
            SELECT
              SUM(good_qty * sam_per_unit),
              SUM(manpower_used * worked_hours * 60)
            FROM production_daily
        """).fetchone()
    finally:
        con.close()

    assert result["std_minutes"] == round(float(std_min), 2)
    assert result["actual_minutes"] == round(float(actual_min), 2)
    assert result["efficiency_pct"] == round(std_min / actual_min * 100.0, 2)


def test_efficiency_in_plausible_range():
    result = line_efficiency_pct()
    assert result["efficiency_pct"] is not None
    # Our data model produces low percentages by design (single-style SAM).
    # Anything in [3, 100] is plausible; we check for > 1 to catch a bug.
    assert 1.0 <= result["efficiency_pct"] <= 100.0, (
        f"efficiency {result['efficiency_pct']} % is outside a plausible range"
    )


# ---------- KPI 4: Productivity ----------
def test_productivity_matches_independent_query():
    result = labor_productivity_pcs_per_hr()

    con = get_connection()
    try:
        good, wh = con.execute("""
            SELECT SUM(good_qty), SUM(manpower_used * worked_hours)
            FROM production_daily
        """).fetchone()
    finally:
        con.close()

    assert result["good_qty"] == good
    assert result["worker_hours"] == round(float(wh), 2)
    assert result["productivity_pcs_per_hr"] == round(good / wh, 3)


def test_productivity_positive():
    result = labor_productivity_pcs_per_hr()
    assert result["productivity_pcs_per_hr"] is not None
    assert result["productivity_pcs_per_hr"] > 0


# ---------- KPI 5: Overtime ----------
def test_overtime_matches_independent_query():
    result = overtime_rate_pct()

    con = get_connection()
    try:
        ot, wh = con.execute("""
            SELECT SUM(overtime_hours), SUM(worked_hours) FROM production_daily
        """).fetchone()
    finally:
        con.close()

    assert result["overtime_hours"] == round(float(ot or 0), 2)
    assert result["worked_hours"] == round(float(wh), 2)
    assert result["overtime_rate_pct"] == round(ot / wh * 100.0, 2)


# ---------- Consistency across filters ----------
def test_line_filter_reduces_n_rows():
    all_n = target_achievement_pct()["n_rows"]
    one_line_n = target_achievement_pct(KpiFilter(line_id="LN-01"))["n_rows"]
    assert one_line_n < all_n
    assert one_line_n > 0


def test_date_range_filter():
    march = all_production_kpis(KpiFilter(
        date_from="2026-03-01", date_to="2026-03-31"))
    all_data = all_production_kpis()
    assert march["target_achievement"]["n_rows"] <= all_data["target_achievement"]["n_rows"]
    assert march["target_achievement"]["n_rows"] > 0


def test_all_five_kpis_return_same_row_count():
    kpis = all_production_kpis()
    counts = {
        kpis["target_achievement"]["n_rows"],
        kpis["variance"]["n_rows"],
        kpis["efficiency"]["n_rows"],
        kpis["productivity"]["n_rows"],
        kpis["overtime"]["n_rows"],
    }
    assert len(counts) == 1, f"row count mismatch across KPIs: {counts}"


# ---------- Formula sanity: sum-first, divide-second ----------
def test_averaging_daily_pct_differs_from_correct_when_volumes_differ():
    """
    Prove the classic trap: averaging daily percentages ≠ aggregate percentage
    whenever planned volumes differ. This test exists to document the trap.
    """
    con = get_connection()
    try:
        rows = con.execute("""
            SELECT planned_qty, actual_qty FROM production_daily
            WHERE planned_qty > 0 AND actual_qty > 0
        """).fetchall()
    finally:
        con.close()

    daily_pcts = [a / p * 100 for p, a in rows if p > 0]
    avg_of_daily = sum(daily_pcts) / len(daily_pcts)

    total_p = sum(p for p, a in rows)
    total_a = sum(a for p, a in rows)
    aggregate_pct = total_a / total_p * 100

    # They should differ by at least 0.1 pp on this data (random volumes).
    # If not, the data is suspiciously uniform — flag it.
    assert abs(avg_of_daily - aggregate_pct) > 0.1, (
        "Data too uniform — averaging trap is not being exercised. "
        "This may indicate a regression in the generator."
    )