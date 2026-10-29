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

check("quality_inspection: rework + rejected <= defective",
      (qc["rework_qty"] + qc["rejected_qty"] <= qc["defective_qty"]).all())

dt = dfs["machine_downtime"]
check("machine_downtime: duration > 0",
      (dt["duration_minutes"] > 0).all())

check("shipments: on_time = (ship <= promised)",
      (shp["on_time"] == (pd.to_datetime(shp["ship_date"]) <=
                          pd.to_datetime(shp["promised_date"]))).all())

check("sales_revenue: recognized <= invoice",
      (rev["recognized_amount_usd"] <= rev["invoice_amount_usd"]).all())

check("sales_revenue: cash <= recognized",
      (rev["cash_received_usd"] <= rev["recognized_amount_usd"]).all())

la = dfs["labor_attendance"]
expected_wage = (
    la["hours_worked"] * la["wage_rate_usd_per_hour"]
    + la["overtime_hours"] * la["wage_rate_usd_per_hour"] * 1.5
)
check("labor_attendance: wage = hours*rate + OT*rate*1.5",
      ((la["total_wage_usd"] - expected_wage).abs() < 0.02).all())

# --- Scenario coverage ---
# Need at least 1 shortfall
shortfall = int((pd_["actual_qty"] < pd_["planned_qty"]).sum())
check("at least 1 production shortfall day",
      shortfall >= 1, f"{shortfall} shortfall rows")

# Need at least 1 late shipment
late = int((~shp["on_time"]).sum())
check("at least 1 late shipment", late >= 1, f"{late} late")

# Need at least 1 outstanding receivable
pending = int(((rev["cash_received_usd"] < rev["recognized_amount_usd"])).sum())
check("at least 1 outstanding receivable", pending >= 1, f"{pending} pending")

# Need downtime variety
check("downtime has >=3 distinct reasons",
      dt["reason_category"].nunique() >= 3,
      f"{dt['reason_category'].nunique()} reasons")

# --- Date sanity ---
for name in ["production_daily", "quality_inspection", "expenses"]:
    df = dfs[name]
    date_col = {"production_daily": "production_date",
                "quality_inspection": "inspection_date",
                "expenses": "expense_date"}[name]
    dates = pd.to_datetime(df[date_col])
    check(f"{name}: no future dates",
          (dates <= pd.Timestamp.today()).all())

# --- Summary ---
print("\n" + "=" * 50)
print(f"RESULT: {ok} passed, {fail} failed")
print("=" * 50)
if fail == 0:
    print("✅ Day 4 transactional data verified.")
    sys.exit(0)
else:
    print("❌ Fix items above, then re-run verify_transactional_data.py")
    sys.exit(1)