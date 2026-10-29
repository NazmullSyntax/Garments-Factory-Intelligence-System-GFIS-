"""
GFIS Day 4 verifier.

Checks the 13 transactional CSVs exist, have correct schema,
referential integrity to Day 3 masters, and business-rule consistency.

Run after generate_transactional_data.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
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


print("\n=== GFIS Day 4 Transactional Verification ===\n")

# --- Load masters for FK validation ---
buyers = pd.read_csv(SAMPLE / "buyers.csv")
styles = pd.read_csv(SAMPLE / "styles.csv")
orders = pd.read_csv(SAMPLE / "orders.csv")

order_ids = set(orders["order_id"])
style_ids = set(styles["style_id"])
buyer_ids = set(buyers["buyer_id"])

# --- Load transactional files ---
files = [
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

dfs = {}
for name in files:
    p = SAMPLE / f"{name}.csv"
    if not p.exists():
        check(f"{name}.csv exists", False, "missing")
        continue
    dfs[name] = pd.read_csv(p)
    check(f"{name}.csv exists", True, f"{len(dfs[name])} rows")

if len(dfs) < len(files):
    print("\n❌ Missing files — run generate_transactional_data.py")
    sys.exit(1)

# --- No empty tables ---
for name, df in dfs.items():
    check(f"{name} has rows", len(df) > 0, f"{len(df)} rows")

# --- Referential integrity ---
pp = dfs["production_plan"]
pd_ = dfs["production_daily"]
qc = dfs["quality_inspection"]
exp = dfs["expenses"]
rev = dfs["sales_revenue"]
shp = dfs["shipments"]

check("production_plan order_id all valid",
      set(pp["order_id"]).issubset(order_ids),
      f"orphans: {set(pp['order_id']) - order_ids}")
check("production_daily order_id all valid",
      set(pd_["order_id"]).issubset(order_ids))
check("quality_inspection order_id all valid",
      set(qc["order_id"]).issubset(order_ids))
check("sales_revenue order_id all valid",
      set(rev["order_id"]).issubset(order_ids))
check("shipments order_id all valid",
      set(shp["order_id"]).issubset(order_ids))

# --- Business rules ---
check("production_daily: good + reject = actual",
      (pd_["good_qty"] + pd_["reject_qty"] == pd_["actual_qty"]).all())

check("quality_inspection: defective <= inspected",
      (qc["defective_qty"] <= qc["inspected_qty"]).all())

check("quality_in