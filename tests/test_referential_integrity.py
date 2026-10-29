"""
Referential-integrity tests: no orphan foreign keys.

Catches: silently dropped rows in joins (the #1 cause of under-reported KPIs).
"""
from __future__ import annotations

import pytest

# Each tuple: (child_table, child_fk, parent_table, parent_pk)
FK_PAIRS = [
    ("orders", "buyer_id", "buyers", "buyer_id"),
    ("orders", "style_id", "styles", "style_id"),
    ("cost_standards", "style_id", "styles", "style_id"),
    ("production_plan", "order_id", "orders", "order_id"),
    ("production_plan", "style_id", "styles", "style_id"),
    ("production_daily", "order_id", "orders", "order_id"),
    ("production_daily", "style_id", "styles", "style_id"),
    ("quality_inspection", "order_id", "orders", "order_id"),
    ("quality_inspection", "style_id", "styles", "style_id"),
    ("sales_revenue", "order_id", "orders", "order_id"),
    ("shipments", "order_id", "orders", "order_id"),
]


@pytest.mark.parametrize("child,child_fk,parent,parent_pk", FK_PAIRS)
def test_fk_integrity(con, child, child_fk, parent, parent_pk):
    """No rows in child with a FK value not present in parent."""
    orphan_count = con.execute(f"""
        SELECT COUNT(*)
        FROM {child} c
        LEFT JOIN {parent} p ON c.{child_fk} = p.{parent_pk}
        WHERE p.{parent_pk} IS NULL
    """).fetchone()[0]
    assert orphan_count == 0, (
        f"{child}.{child_fk} → {parent}.{parent_pk}: {orphan_count} orphans"
    )


def test_cost_standards_cover_all_styles(con):
    """Every style must have exactly one cost_standards row."""
    missing = con.execute("""
        SELECT COUNT(*) FROM styles s
        LEFT JOIN cost_standards cs ON s.style_id = cs.style_id
        WHERE cs.style_id IS NULL
    """).fetchone()[0]
    assert missing == 0, f"{missing} styles without cost standards"