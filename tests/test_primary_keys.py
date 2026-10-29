"""
Primary-key uniqueness tests.

Catches: double-counting (e.g., the same order appearing twice = 2x revenue).
"""
from __future__ import annotations

import pytest

PK_TABLES = {
    "buyers": "buyer_id",
    "styles": "style_id",
    "cost_standards": "style_id",
    "orders": "order_id",
    "quality_inspection": "inspection_id",
    "machine_downtime": "downtime_id",
    "maintenance": "maintenance_id",
    "inventory_transactions": "transaction_id",
    "purchase_orders": "po_id",
    "expenses": "expense_id",
    "sales_revenue": "revenue_id",
    "cash_flow": "cf_id",
    "shipments": "shipment_id",
}


@pytest.mark.parametrize("table,pk", sorted(PK_TABLES.items()))
def test_primary_key_unique(con, table, pk):
    dup_count = con.execute(f"""
        SELECT COUNT(*) FROM (
            SELECT {pk} FROM {table}
            GROUP BY {pk} HAVING COUNT(*) > 1
        )
    """).fetchone()[0]
    assert dup_count == 0, f"{table}.{pk}: {dup_count} duplicate values"


@pytest.mark.parametrize("table,pk", sorted(PK_TABLES.items()))
def test_primary_key_not_null(con, table, pk):
    null_count = con.execute(
        f"SELECT COUNT(*) FROM {table} WHERE {pk} IS NULL"
    ).fetchone()[0]
    assert null_count == 0, f"{table}.{pk}: {null_count} NULL values"