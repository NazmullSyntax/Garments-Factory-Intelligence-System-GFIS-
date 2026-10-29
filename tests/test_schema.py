"""
Schema tests: every expected table and required column is present.

Catches: schema drift, accidental table drops, missing migrations.
"""
from __future__ import annotations

import pytest

EXPECTED_TABLES = {
    "buyers", "styles", "cost_standards", "orders",
    "production_plan", "production_daily", "labor_attendance",
    "quality_inspection", "machine_downtime", "maintenance",
    "inventory_transactions", "purchase_orders", "expenses",
    "sales_revenue", "cash_flow", "budget", "shipments",
}

REQUIRED_COLUMNS = {
    "buyers": ["buyer_id", "buyer_name", "country", "payment_terms_days"],
    "orders": ["order_id", "buyer_id", "style_id", "order_date",
               "delivery_date", "order_qty", "unit_price_usd",
               "total_value_usd", "status"],
    "production_daily": ["production_date", "line_id", "shift",
                         "order_id", "style_id", "planned_qty",
                         "actual_qty", "good_qty", "reject_qty",
                         "sam_per_unit"],
    "quality_inspection": ["inspection_id", "inspection_date", "order_id",
                           "inspected_qty", "defective_qty", "rework_qty",
                           "rejected_qty", "defect_category"],
    "sales_revenue": ["revenue_id", "order_id", "invoice_amount_usd",
                      "recognized_amount_usd", "cash_received_usd"],
    "shipments": ["shipment_id", "order_id", "ship_date", "promised_date",
                  "on_time", "delay_days"],
}


@pytest.mark.parametrize("table_name", sorted(EXPECTED_TABLES))
def test_table_exists(tables, table_name):
    assert table_name in tables, f"table '{table_name}' missing"


@pytest.mark.parametrize("table_name,required", sorted(REQUIRED_COLUMNS.items()))
def test_required_columns(con, table_name, required):
    """Every required column must exist in the table."""
    actual = {
        row[0].lower()
        for row in con.execute(f"DESCRIBE {table_name}").fetchall()
    }
    missing = [c for c in required if c.lower() not in actual]
    assert not missing, f"{table_name} missing columns: {missing}"


@pytest.mark.parametrize("table_name", sorted(EXPECTED_TABLES))
def test_table_not_empty(con, table_name):
    count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    assert count > 0, f"{table_name} is empty"