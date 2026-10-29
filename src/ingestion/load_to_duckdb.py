"""
GFIS — Day 5 DuckDB loader.

Reads all 15 CSVs from data/sample/ and loads them into a single
DuckDB database at data/gfis.duckdb.

Recreates the DB from scratch on each run, so this is idempotent:
the file is deleted first, then all tables are created and loaded.

Run:  python -m src.ingestion.load_to_duckdb
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE = PROJECT_ROOT / "data" / "sample"
DB_PATH = PROJECT_ROOT / "data" / "gfis.duckdb"
SCHEMA_SQL = PROJECT_ROOT / "sql" / "schema.sql"

# Every CSV we need. Table name == filename without .csv
TABLES = [
    "buyers",
    "styles",
    "cost_standards",
    "orders",
    "production_plan",
    "production_daily",
    "labor_attendance",
    "quality_inspection",
    "machine_downtime",
    "maintenance",
    "inventory_transactions",
    "purchase_orders",
    "expenses",
    "sales_revenue",
    "cash_flow",
    "budget",
    "shipments",
]

# Column-dtype overrides so DuckDB doesn't misinfer booleans/dates
DATE_COLUMNS = {
    "orders": ["order_date", "delivery_date"],
    "production_plan": ["plan_date"],
    "production_daily": ["production_date"],
    "labor_attendance": ["attendance_date"],
    "quality_inspection": ["inspection_date"],
    "machine_downtime": ["start_time", "end_time"],
    "maintenance": ["maintenance_date"],
    "inventory_transactions": ["transaction_date"],
    "purchase_orders": ["po_date", "promised_date", "actual_receipt_date"],
    "expenses": ["expense_date"],
    "sales_revenue": ["invoice_date", "recognized_date", "cash_received_date"],
    "cash_flow": ["period_date"],
    "budget": ["budget_month"],
    "shipments": ["ship_date", "promised_date"],
    "styles": ["effective_from"],
    "cost_standards": ["effective_from"],
}

BOOL_COLUMNS = {
    "orders": ["delivery_risk_flag", "margin_squeeze_flag"],
    "labor_attendance": ["present"],
    "shipments": ["on_time"],
}


def load_csv(table: str) -> pd.DataFrame:
    path = SAMPLE / f"{table}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing CSV: {path}")

    df = pd.read_csv(path)

    for col in DATE_COLUMNS.get(table, []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date

    for col in BOOL_COLUMNS.get(table, []):
        if col in df.columns:
            df[col] = df[col].astype("boolean")

    return df


def main() -> None:
    print("=" * 55)
    print("GFIS Day 5 — DuckDB Loader")
    print(f"DB path: {DB_PATH}")
    print("=" * 55)

    # 1. Delete old DB (idempotent)
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"[OK] Removed old DB")

    # 2. Connect (creates file)
    con = duckdb.connect(str(DB_PATH))
    print(f"[OK] Created new DB")

    # 3. Apply schema
    schema_sql = SCHEMA_SQL.read_text(encoding="utf-8")
    con.execute(schema_sql)
    print(f"[OK] Applied schema ({len(schema_sql)} chars)")

    # 4. Load each table
    total_rows = 0
    for table in TABLES:
        df = load_csv(table)
        con.register("df_temp", df)
        con.execute(f"INSERT INTO {table} SELECT * FROM df_temp")
        con.unregister("df_temp")
        count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"[OK] {table:<25} {count:>6} rows")
        total_rows += count

    # 5. Sanity check — count tables
    result = con.execute("""
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema = 'main'
    """).fetchone()[0]
    print(f"[OK] {result} tables in database")

    con.close()

    print("=" * 55)
    print(f"Total rows loaded: {total_rows}")
    print(f"DB file size: {DB_PATH.stat().st_size:,} bytes")
    print("Day 5 load complete.")
    print("=" * 55)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)