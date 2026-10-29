"""
Business-rule tests: the 10 data-quality rules from data_dictionary.md.

Catches: arithmetic that looks plausible but is wrong (the deadliest class
of bug — KPIs will compute, but they'll be silently incorrect).
"""
from __future__ import annotations

import pytest


# ---------- Rule 3: production arithmetic ----------
def test_production_good_plus_reject_equals_actual(con):
    bad = con.execute("""
        SELECT COUNT(*) FROM production_daily
        WHERE good_qty + reject_qty != actual_qty
    """).fetchone()[0]
    assert bad == 0, f"{bad} rows where good + reject ≠ actual"


def test_production_actual_non_negative(con):
    bad = con.execute("""
        SELECT COUNT(*) FROM production_daily
        WHERE actual_qty < 0 OR good_qty < 0 OR reject_qty < 0
    """).fetchone()[0]
    assert bad == 0, f"{bad} rows with negative quantities"


# ---------- Rule 4: quality arithmetic ----------
def test_quality_defective_lte_inspected(con):
    bad = con.execute("""
        SELECT COUNT(*) FROM quality_inspection
        WHERE defective_qty > inspected_qty
    """).fetchone()[0]
    assert bad == 0, f"{bad} rows with defective > inspected"


def test_quality_rework_plus_rejected_lte_defective(con):
    bad = con.execute("""
        SELECT COUNT(*) FROM quality_inspection
        WHERE rework_qty + rejected_qty > defective_qty
    """).fetchone()[0]
    assert bad == 0, f"{bad} rows where rework + rejected > defective"


def test_quality_all_non_negative(con):
    bad = con.execute("""
        SELECT COUNT(*) FROM quality_inspection
        WHERE inspected_qty < 0 OR defective_qty < 0
              OR rework_qty < 0 OR rejected_qty < 0
    """).fetchone()[0]
    assert bad == 0, f"{bad} rows with negative quantities"


# ---------- Rule 5: shipment on_time flag ----------
def test_shipment_on_time_consistent_with_dates(con):
    bad = con.execute("""
        SELECT COUNT(*) FROM shipments
        WHERE on_time != (ship_date <= promised_date)
    """).fetchone()[0]
    assert bad == 0, f"{bad} rows with inconsistent on_time flag"


def test_shipment_delay_days_non_negative(con):
    bad = con.execute("""
        SELECT COUNT(*) FROM shipments
        WHERE delay_days < 0
    """).fetchone()[0]
    assert bad == 0, f"{bad} rows with negative delay_days"


def test_shipment_delay_days_matches_dates(con):
    bad = con.execute("""
        SELECT COUNT(*) FROM shipments
        WHERE delay_days != GREATEST(0, DATE_DIFF('day', promised_date, ship_date))
    """).fetchone()[0]
    assert bad == 0, f"{bad} rows where delay_days ≠ date difference"


# ---------- Rule 6: downtime duration ----------
def test_downtime_duration_matches_timestamps(con):
    bad = con.execute("""
        SELECT COUNT(*) FROM machine_downtime
        WHERE duration_minutes != DATE_DIFF('minute', start_time, end_time)
    """).fetchone()[0]
    assert bad == 0, f"{bad} rows where duration ≠ end − start"


def test_downtime_positive_duration(con):
    bad = con.execute("""
        SELECT COUNT(*) FROM machine_downtime
        WHERE duration_minutes <= 0 OR end_time <= start_time
    """).fetchone()[0]
    assert bad == 0, f"{bad} rows with non-positive duration"


# ---------- Rule 7: labor wage formula ----------
def test_labor_wage_formula(con):
    bad = con.execute("""
        SELECT COUNT(*) FROM labor_attendance
        WHERE ABS(
            total_wage_usd
            - (hours_worked * wage_rate_usd_per_hour
               + overtime_hours * wage_rate_usd_per_hour * 1.5)
        ) > 0.02
    """).fetchone()[0]
    assert bad == 0, f"{bad} rows where wage formula is off by > $0.02"


def test_labor_hours_non_negative(con):
    bad = con.execute("""
        SELECT COUNT(*) FROM labor_attendance
        WHERE hours_worked < 0 OR overtime_hours < 0
              OR wage_rate_usd_per_hour <= 0
    """).fetchone()[0]
    assert bad == 0, f"{bad} rows with bad hours/rate"


# ---------- Rule 8: all USD amounts non-negative ----------
@pytest.mark.parametrize("table,column", [
    ("orders", "unit_price_usd"),
    ("orders", "total_value_usd"),
    ("orders", "fabric_cost_usd"),
    ("orders", "cm_cost_usd"),
    ("expenses", "amount_usd"),
    ("sales_revenue", "invoice_amount_usd"),
    ("sales_revenue", "recognized_amount_usd"),
    ("sales_revenue", "cash_received_usd"),
    ("purchase_orders", "unit_price_usd"),
    ("maintenance", "cost_usd"),
    ("budget", "budgeted_amount_usd"),
])
def test_usd_amounts_non_negative(con, table, column):
    bad = con.execute(
        f"SELECT COUNT(*) FROM {table} WHERE {column} < 0"
    ).fetchone()[0]
    assert bad == 0, f"{table}.{column}: {bad} negative values"


# ---------- Rule 9: date ordering ----------
def test_order_dates_ordered(con):
    bad = con.execute("""
        SELECT COUNT(*) FROM orders
        WHERE delivery_date < order_date
    """).fetchone()[0]
    assert bad == 0, f"{bad} orders with delivery before order date"


def test_revenue_dates_ordered(con):
    bad = con.execute("""
        SELECT COUNT(*) FROM sales_revenue
        WHERE recognized_date < invoice_date
    """).fetchone()[0]
    assert bad == 0, f"{bad} revenues recognized before invoice"


def test_cash_after_recognition(con):
    bad = con.execute("""
        SELECT COUNT(*) FROM sales_revenue
        WHERE cash_received_date IS NOT NULL
          AND cash_received_date < recognized_date
    """).fetchone()[0]
    assert bad == 0, f"{bad} revenues where cash arrived before recognition"


# ---------- Revenue ≤ invoice rule ----------
def test_recognized_lte_invoice(con):
    bad = con.execute("""
        SELECT COUNT(*) FROM sales_revenue
        WHERE recognized_amount_usd > invoice_amount_usd
    """).fetchone()[0]
    assert bad == 0, f"{bad} rows where recognized > invoice"


def test_cash_lte_recognized(con):
    bad = con.execute("""
        SELECT COUNT(*) FROM sales_revenue
        WHERE cash_received_usd > recognized_amount_usd
    """).fetchone()[0]
    assert bad == 0, f"{bad} rows where cash > recognized"


# ---------- Order arithmetic ----------
def test_order_total_matches_price_times_qty(con):
    bad = con.execute("""
        SELECT COUNT(*) FROM orders
        WHERE ABS(total_value_usd - unit_price_usd * order_qty) > 0.02
    """).fetchone()[0]
    assert bad == 0, f"{bad} orders where total ≠ price × qty"


def test_order_qty_positive(con):
    bad = con.execute(
        "SELECT COUNT(*) FROM orders WHERE order_qty <= 0"
    ).fetchone()[0]
    assert bad == 0, f"{bad} orders with non-positive qty"


# ---------- Enum domain checks ----------
def test_order_status_valid(con):
    valid = {"Open", "InProduction", "Shipped", "Closed", "Cancelled"}
    rows = con.execute("SELECT DISTINCT status FROM orders").fetchall()
    actual = {r[0] for r in rows}
    invalid = actual - valid
    assert not invalid, f"invalid order.status values: {invalid}"


def test_defect_category_valid(con):
    valid = {"Stitch", "Measurement", "Fabric", "Stain", "Trimming", "Other"}
    rows = con.execute(
        "SELECT DISTINCT defect_category FROM quality_inspection"
    ).fetchall()
    invalid = {r[0] for r in rows} - valid
    assert not invalid, f"invalid defect categories: {invalid}"


def test_downtime_reason_valid(con):
    valid = {"Breakdown", "Changeover", "MaterialShortage",
             "NoOperator", "Power", "Scheduled"}
    rows = con.execute(
        "SELECT DISTINCT reason_category FROM machine_downtime"
    ).fetchall()
    invalid = {r[0] for r in rows} - valid
    assert not invalid, f"invalid downtime reasons: {invalid}"


def test_shipment_mode_valid(con):
    rows = con.execute("SELECT DISTINCT shipment_mode FROM shipments").fetchall()
    invalid = {r[0] for r in rows} - {"Sea", "Air"}
    assert not invalid, f"invalid shipment modes: {invalid}"