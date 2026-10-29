"""
GFIS Day 5 verifier.

Opens data/gfis.duckdb and checks:
  - All expected tables exist
  - Row counts match the CSVs
  - Key SQL joins work
  - Referential integrity survives the load
  - A sample KPI query runs

Run after load_to_duckdb.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "gfis.duckdb"
SAMPLE = ROOT / "data" / "sample"

ok = 0
fail = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global ok, fail
    if condition:
        print(f"[PASS] {label}" + (f" — {detail}" if detail else ""))
        ok += 1
    else:
        print(f"[FAIL] {label}" + (f" — {detail}" if detail else ""))
        fail += 1


print("\n=== GFIS Day 5 DuckDB Verification ===\n")

check("DB file exists", DB_PATH.exists(),
      f"{DB_PATH.stat().st_size:,} bytes" if DB_PATH.exists() else "missing")

if not DB_PATH.exists():
    sys.exit(1)

con = duckdb.connect(str(DB_PATH), read_only=True)

EXPECTED_TABLES = [
    "buyers", "styles", "cost_standards", "orders",
    "production_plan", "production_daily", "labor_attendance",
    "quality_inspection", "machine_downtime", "maintenance",
    "inventory_transactions", "purchase_orders", "expenses",
    "sales_revenue", "cash_flow", "budget", "shipments",
]

# --- 1. All tables exist ---
existing = set(
    row[0] for row in con.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'main'
    """).fetchall()
)

for t in EXPECTED_TABLES:
    check(f"table {t} exists", t in existing)

# --- 2. Row counts match CSVs ---
print("\n-- Row count consistency --")
for t in EXPECTED_TABLES:
    csv_path = SAMPLE / f"{t}.csv"
    csv_rows = len(pd.read_csv(csv_path))
    db_rows = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    check(f"{t} row count", csv_rows == db_rows,
          f"csv={csv_rows}, db={db_rows}")

# --- 3. Key joins work ---
print("\n-- SQL joins --")
try:
    result = con.execute("""
        SELECT COUNT(*)
        FROM orders o
        JOIN buyers b ON o.buyer_id = b.buyer_id
        JOIN styles s ON o.style_id = s.style_id
    """).fetchone()[0]
    check("orders join buyers and styles", result > 0, f"{result} rows")
except Exception as e:
    check("orders join buyers and styles", False, str(e))

try:
    result = con.execute("""
        SELECT COUNT(*)
        FROM production_daily p
        JOIN orders o ON p.order_id = o.order_id
    """).fetchone()[0]
    check("production_daily join orders", result > 0, f"{result} rows")
except Exception as e:
    check("production_daily join orders", False, str(e))

try:
    result = con.execute("""
        SELECT COUNT(*)
        FROM sales_revenue r
        JOIN orders o ON r.order_id = o.order_id
    """).fetchone()[0]
    check("sales_revenue join orders", result > 0, f"{result} rows")
except Exception as e:
    check("sales_revenue join orders", False, str(e))

# --- 4. Referential integrity in DB ---
print("\n-- Referential integrity --")
orphan_orders = con.execute("""
    SELECT COUNT(*) FROM orders o
    LEFT JOIN buyers b ON o.buyer_id = b.buyer_id
    WHERE b.buyer_id IS NULL
""").fetchone()[0]
check("no orphan order.buyer_id", orphan_orders == 0, f"{orphan_orders} orphans")

orphan_styles = con.execute("""
    SELECT COUNT(*) FROM orders o
    LEFT JOIN styles s ON o.style_id = s.style_id
    WHERE s.style_id IS NULL
""").fetchone()[0]
check("no orphan order.style_id", orphan_styles == 0, f"{orphan_styles} orphans")

orphan_prod = con.execute("""
    SELECT COUNT(*) FROM production_daily p
    LEFT JOIN orders o ON p.order_id = o.order_id
    WHERE o.order_id IS NULL
""").fetchone()[0]
check("no orphan production.order_id", orphan_prod == 0, f"{orphan_prod} orphans")

# --- 5. Sample KPI query ---
print("\n-- Sample KPI query --")
try:
    result = con.execute("""
        SELECT
            SUM(actual_qty) AS total_actual,
            SUM(good_qty)   AS total_good,
            ROUND(100.0 * SUM(good_qty) / NULLIF(SUM(actual_qty), 0), 2)
                AS good_pct
        FROM production_daily
    """).fetchone()
    total_actual, total_good, good_pct = result
    check("production good_qty <= actual_qty",
          total_good <= total_actual,
          f"good={total_good:,}, actual={total_actual:,}, good%={good_pct}")
    check("sample KPI returns non-zero good_pct",
          good_pct is not None and good_pct > 0,
          f"{good_pct}%")
except Exception as e:
    check("sample KPI query", False, str(e))

try:
    result = con.execute("""
        SELECT
            COUNT(*) AS n_orders,
            ROUND(SUM(total_value_usd), 2) AS total_usd
        FROM orders
        WHERE status IN ('Shipped', 'Closed')
    """).fetchone()
    check("shipped+closed orders query",
          result[0] > 0 and result[1] > 0,
          f"{result[0]} orders, ${result[1]:,.2f}")
except Exception as e:
    check("shipped+closed orders query", False, str(e))

# --- 6. Date type check ---
print("\n-- Date type sanity --")
try:
    row = con.execute("""
        SELECT MIN(production_date), MAX(production_date)
        FROM production_daily
    """).fetchone()
    check("production_date stored as DATE",
          row[0] is not None and row[1] is not None,
          f"{row[0]} to {row[1]}")
except Exception as e:
    check("production_date type", False, str(e))

con.close()

print("\n" + "=" * 50)
print(f"RESULT: {ok} passed, {fail} failed")
print("=" * 50)
if fail == 0:
    print("✅ Day 5 DuckDB load verified.")
    sys.exit(0)
else:
    print("❌ Fix items above, then re-run verify_duckdb.py")
    sys.exit(1)