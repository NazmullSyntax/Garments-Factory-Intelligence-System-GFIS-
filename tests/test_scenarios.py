"""
Scenario-coverage tests: verify the synthetic data actually contains the
business problems we intentionally injected.

Catches: "the demo has nothing interesting to show" (a surprisingly common
failure when seeds or distributions drift).
"""
from __future__ import annotations


def test_at_least_one_production_shortfall(con):
    """Root-cause engine needs something to find."""
    count = con.execute("""
        SELECT COUNT(*) FROM production_daily
        WHERE actual_qty < planned_qty * 0.95
    """).fetchone()[0]
    assert count > 0, "no meaningful production shortfall exists"


def test_at_least_one_late_shipment(con):
    count = con.execute("""
        SELECT COUNT(*) FROM shipments WHERE on_time = FALSE
    """).fetchone()[0]
    assert count > 0, "no late shipments exist"


def test_at_least_one_outstanding_receivable(con):
    count = con.execute("""
        SELECT COUNT(*) FROM sales_revenue
        WHERE cash_received_usd < recognized_amount_usd
    """).fetchone()[0]
    assert count > 0, "no outstanding receivables exist"


def test_at_least_one_margin_squeeze_order(con):
    count = con.execute("""
        SELECT COUNT(*) FROM orders WHERE margin_squeeze_flag = TRUE
    """).fetchone()[0]
    assert count > 0, "no margin-squeezed orders exist"


def test_at_least_one_delivery_risk_order(con):
    count = con.execute("""
        SELECT COUNT(*) FROM orders WHERE delivery_risk_flag = TRUE
    """).fetchone()[0]
    assert count > 0, "no delivery-risk orders exist"


def test_downtime_has_variety(con):
    """Multiple downtime reasons → root-cause engine has real signal."""
    n = con.execute("""
        SELECT COUNT(DISTINCT reason_category) FROM machine_downtime
    """).fetchone()[0]
    assert n >= 3, f"only {n} distinct downtime reasons"


def test_quality_has_defects(con):
    rate = con.execute("""
        SELECT SUM(defective_qty)::DOUBLE / NULLIF(SUM(inspected_qty), 0)
        FROM quality_inspection
    """).fetchone()[0]
    assert rate is not None and rate > 0, "no defects at all"


def test_overtime_exists_but_not_everywhere(con):
    """Realistic: some OT, but not 100% of workers every day."""
    row = con.execute("""
        SELECT
            SUM(CASE WHEN overtime_hours > 0 THEN 1 ELSE 0 END)::DOUBLE
              / COUNT(*) AS ot_share
        FROM labor_attendance
        WHERE present = TRUE
    """).fetchone()[0]
    assert 0.05 <= row <= 0.50, (
        f"overtime share {row:.2%} outside realistic 5-50% band"
    )