"""
GFIS Day 3 verifier.

Checks that the 4 master CSVs exist, have correct schema, and satisfy
referential integrity + business-scenario coverage.

Run after generate_master_data.py.
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


print("\n=== GFIS Day 3 Master-Data Verification ===\n")

# --- Load ---
files = {
    "buyers": "buyers.csv",
    "styles": "styles.csv",
    "cost_standards": "cost_standards.csv",
    "orders": "orders.csv",
}
dfs = {}

for key, fname in files.items():
    p = SAMPLE / fname
    if not p.exists():
        check(f"{fname} exists", False, "file not found")
        continue
    dfs[key] = pd.read_csv(p)
    check(f"{fname} exists", True, f"{p.stat().st_size} bytes")

if len(dfs) < 4:
    print("\n❌ Missing files — cannot continue. Run generate_master_data.py")
    sys.exit(1)

# --- Row counts ---
check("buyers has 8 rows", len(dfs["buyers"]) == 8, f"got {len(dfs['buyers'])}")
check("styles has 40 rows", len(dfs["styles"]) == 40, f"got {len(dfs['styles'])}")
check("cost_standards has 40 rows", len(dfs["cost_standards"]) == 40,
      f"got {len(dfs['cost_standards'])}")
check("orders has 120 rows", len(dfs["orders"]) == 120, f"got {len(dfs['orders'])}")

# --- Schema check ---
REQUIRED = {
    "buyers": ["buyer_id", "buyer_name", "country", "payment_terms_days"],
    "styles": ["style_id", "style_name", "product_type", "sam_per_unit",
               "standard_fabric_meters", "standard_unit_cost_usd",
               "target_selling_price_usd"],
    "cost_standards": ["style_id", "sam_per_unit", "standard_fabric_meters",
                       "standard_fabric_cost_usd", "standard_cm_cost_usd",
                       "standard_unit_cost_usd", "effective_from"],
    "orders": ["order_id", "buyer_id", "style_id", "order_date", "delivery_date",
               "order_qty", "unit_price_usd", "total_value_usd", "status",
               "fabric_cost_usd", "cm_cost_usd", "payment_terms_days"],
}

for key, cols in REQUIRED.items():
    missing = [c for c in cols if c not in dfs[key].columns]
    check(f"{key} schema", not missing, f"missing: {missing}" if missing else "all present")

# --- PK uniqueness ---
check("buyer_id unique", dfs["buyers"]["buyer_id"].is_unique)
check("style_id unique", dfs["styles"]["style_id"].is_unique)
check("cost_standards.style_id unique", dfs["cost_standards"]["style_id"].is_unique)
check("order_id unique", dfs["orders"]["order_id"].is_unique)

# --- Referential integrity ---
buyer_ids = set(dfs["buyers"]["buyer_id"])
style_ids = set(dfs["styles"]["style_id"])
cs_style_ids = set(dfs["cost_standards"]["style_id"])

orders_buyers = set(dfs["orders"]["buyer_id"])
orders_styles = set(dfs["orders"]["style_id"])

check("all order.buyer_id exist in buyers",
      orders_buyers.issubset(buyer_ids),
      f"orphans: {orders_buyers - buyer_ids}")
check("all order.style_id exist in styles",
      orders_styles.issubset(style_ids),
      f"orphans: {orders_styles - style_ids}")
check("cost_standards.style_id matches styles",
      cs_style_ids == style_ids,
      f"diff: {cs_style_ids ^ style_ids}")

# --- Business rules ---
o = dfs["orders"]
check("all prices > 0", (o["unit_price_usd"] > 0).all())
check("all qty > 0", (o["order_qty"] > 0).all())
check("total = price * qty (tolerance 0.02)",
      ((o["total_value_usd"] - o["unit_price_usd"] * o["order_qty"]).abs() < 0.02).all())
check("delivery_date >= order_date",
      (pd.to_datetime(o["delivery_date"]) >= pd.to_datetime(o["order_date"])).all())

valid_statuses = {"Open", "InProduction", "Shipped", "Closed", "Cancelled"}
check("all statuses valid",
      set(o["status"]) <= valid_statuses,
      f"unexpected: {set(o['status']) - valid_statuses}")

# --- Scenario coverage ---
if "delivery_risk_flag" in o.columns:
    risk = int(o["delivery_risk_flag"].sum())
    check("at least 1 delivery-risk order", risk >= 1, f"{risk} flagged")

if "margin_squeeze_flag" in o.columns:
    squeeze = int(o["margin_squeeze_flag"].sum())
    check("at least 1 margin-squeeze order", squeeze >= 1, f"{squeeze} flagged")

# --- Summary ---
print("\n" + "=" * 50)
print(f"RESULT: {ok} passed, {fail} failed")
print("=" * 50)
if fail == 0:
    print("✅ Day 3 master data verified.")
    sys.exit(0)
else:
    print("❌ Fix items above, then re-run verify_master_data.py")
    sys.exit(1)