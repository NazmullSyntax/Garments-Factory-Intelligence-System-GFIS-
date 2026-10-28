"""
GFIS — Day 3 synthetic master data generator.

Generates 4 CSVs into data/sample/:
    buyers.csv, styles.csv, orders.csv, cost_standards.csv

Reproducible: fixed SEED means same files on every run.

⚠️ SYNTHETIC DATA — no real buyers, styles, or factories.
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

# --- Config ---
SEED = 42
random.seed(SEED)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "sample"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Demo window — 6 months
DEMO_START = date(2025, 11, 1)
DEMO_END = date(2026, 4, 30)

# --- Buyer master ---
BUYERS = [
    {"buyer_id": "BUY-01", "buyer_name": "Nordic Apparel AB",
     "country": "Sweden", "payment_terms_days": 60},
    {"buyer_id": "BUY-02", "buyer_name": "Rhine Fashion GmbH",
     "country": "Germany", "payment_terms_days": 45},
    {"buyer_id": "BUY-03", "buyer_name": "Albion Retail Ltd",
     "country": "UK", "payment_terms_days": 30},
    {"buyer_id": "BUY-04", "buyer_name": "Atlantic Denim Co",
     "country": "USA", "payment_terms_days": 60},
    {"buyer_id": "BUY-05", "buyer_name": "Pacific Basics Inc",
     "country": "USA", "payment_terms_days": 45},
    {"buyer_id": "BUY-06", "buyer_name": "Kansai Trading KK",
     "country": "Japan", "payment_terms_days": 30},
    {"buyer_id": "BUY-07", "buyer_name": "Maple Leaf Wear",
     "country": "Canada", "payment_terms_days": 60},
    {"buyer_id": "BUY-08", "buyer_name": "Southern Cross Pty",
     "country": "Australia", "payment_terms_days": 45},
]

# --- Product type templates ---
# (name, sam_min, sam_max, fabric_min, fabric_max,
#  price_min, price_max, fabric_cost_per_m)
PRODUCT_TYPES = [
    ("Basic Tee",     4,   7, 0.8, 1.2,  3.0,  5.0, 3.0),
    ("Polo Shirt",    8,  12, 1.2, 1.5,  5.0,  8.0, 3.5),
    ("Denim Jeans",  18,  25, 1.5, 2.0, 12.0, 18.0, 5.0),
    ("Denim Jacket", 25,  35, 2.0, 2.5, 22.0, 32.0, 5.5),
    ("Hoodie",       15,  22, 1.8, 2.2, 10.0, 16.0, 4.0),
    ("Kids Tee",      3,   5, 0.6, 0.9,  2.0,  3.5, 2.5),
]

LABOR_RATE_USD_PER_MIN = 0.045
OVERHEAD_RATE_PER_SAM = 0.030


def make_buyers() -> pd.DataFrame:
    df = pd.DataFrame(BUYERS)
    df["created_at"] = pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    return df


def make_styles(n_styles: int = 40) -> pd.DataFrame:
    rows = []
    for i in range(1, n_styles + 1):
        ptype = random.choice(PRODUCT_TYPES)
        (name, sam_lo, sam_hi, fab_lo, fab_hi,
         price_lo, price_hi, fabric_cost) = ptype

        sam = round(random.uniform(sam_lo, sam_hi), 1)
        fabric_m = round(random.uniform(fab_lo, fab_hi), 2)
        selling_price = round(random.uniform(price_lo, price_hi), 2)

        fabric_cost_usd = round(fabric_m * fabric_cost, 2)
        cm_cost_usd = round(sam * LABOR_RATE_USD_PER_MIN + sam * OVERHEAD_RATE_PER_SAM, 2)
        unit_cost_usd = round(fabric_cost_usd + cm_cost_usd, 2)

        rows.append({
            "style_id": f"STY-{i:04d}",
            "style_name": f"{name} #{i:03d}",
            "product_type": name,
            "sam_per_unit": sam,
            "standard_fabric_meters": fabric_m,
            "standard_fabric_cost_usd": fabric_cost_usd,
            "standard_cm_cost_usd": cm_cost_usd,
            "standard_unit_cost_usd": unit_cost_usd,
            "target_selling_price_usd": selling_price,
            "effective_from": date(2025, 11, 1),
        })
    return pd.DataFrame(rows)


def make_cost_standards(styles: pd.DataFrame) -> pd.DataFrame:
    df = styles[[
        "style_id",
        "sam_per_unit",
        "standard_fabric_meters",
        "standard_fabric_cost_usd",
        "standard_cm_cost_usd",
        "standard_unit_cost_usd",
        "effective_from",
    ]].copy()
    return df


def make_orders(styles: pd.DataFrame, buyers: pd.DataFrame,
                n_orders: int = 120) -> pd.DataFrame:
    order_rows = []
    buyer_ids = buyers["buyer_id"].tolist()

    for i in range(1, n_orders + 1):
        buyer_id = random.choice(buyer_ids)
        style = styles.sample(n=1, random_state=random.randint(1, 10**6)).iloc[0]

        order_date = DEMO_START + timedelta(days=random.randint(0, 120))

        if random.random() < 0.10:
            lead_days = random.randint(30, 40)
        else:
            lead_days = random.randint(60, 90)
        delivery_date = order_date + timedelta(days=lead_days)

        qty = random.choice([2000, 3000, 5000, 6000, 8000,
                             10000, 12000, 15000, 20000, 25000])

        base_price = style["target_selling_price_usd"]
        unit_price = round(base_price * random.uniform(0.95, 1.10), 2)

        squeezed = random.random() < 0.15
        if squeezed:
            unit_price = round(unit_price * 0.90, 2)

        fabric_cost = style["standard_fabric_cost_usd"] * qty
        cm_cost = style["standard_cm_cost_usd"] * qty

        if squeezed:
            fabric_cost = fabric_cost * 1.10

        fabric_cost = round(fabric_cost, 2)
        cm_cost = round(cm_cost, 2)

        total_value = round(unit_price * qty, 2)

        days_to_delivery = (delivery_date - DEMO_END).days
        if order_date > DEMO_END - timedelta(days=30):
            status = "Open"
        elif days_to_delivery > 30:
            status = random.choices(
                ["InProduction", "Open"], weights=[0.7, 0.3], k=1)[0]
        else:
            status = random.choices(
                ["Shipped", "InProduction", "Closed", "Cancelled"],
                weights=[0.45, 0.30, 0.20, 0.05], k=1)[0]

        order_rows.append({
            "order_id": f"ORD-2026-{i:04d}",
            "buyer_id": buyer_id,
            "style_id": style["style_id"],
            "order_date": order_date,
            "delivery_date": delivery_date,
            "order_qty": qty,
            "unit_price_usd": unit_price,
            "total_value_usd": total_value,
            "status": status,
            "fabric_cost_usd": fabric_cost,
            "cm_cost_usd": cm_cost,
            "payment_terms_days": int(
                buyers.loc[buyers["buyer_id"] == buyer_id,
                           "payment_terms_days"].iloc[0]),
            "delivery_risk_flag": lead_days <= 40,
            "margin_squeeze_flag": squeezed,
        })

    return pd.DataFrame(order_rows)


def main() -> None:
    print("=" * 55)
    print("GFIS Day 3 — Synthetic Master Data Generator")
    print(f"Seed: {SEED}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 55)

    buyers = make_buyers()
    buyers.to_csv(OUTPUT_DIR / "buyers.csv", index=False)
    print(f"[OK] buyers.csv          {len(buyers):>5} rows")

    styles = make_styles(40)
    styles.to_csv(OUTPUT_DIR / "styles.csv", index=False)
    print(f"[OK] styles.csv          {len(styles):>5} rows")

    cost_standards = make_cost_standards(styles)
    cost_standards.to_csv(OUTPUT_DIR / "cost_standards.csv", index=False)
    print(f"[OK] cost_standards.csv  {len(cost_standards):>5} rows")

    orders = make_orders(styles, buyers, n_orders=120)
    orders.to_csv(OUTPUT_DIR / "orders.csv", index=False)
    print(f"[OK] orders.csv          {len(orders):>5} rows")

    print("-" * 55)
    print(f"Buyers:               {len(buyers)}")
    print(f"Styles:               {len(styles)}")
    print(f"Orders:               {len(orders)}")
    print(f"  -> delivery risk:   {int(orders['delivery_risk_flag'].sum())}")
    print(f"  -> margin squeeze:  {int(orders['margin_squeeze_flag'].sum())}")
    print("=" * 55)
    print("Day 3 generation complete.")


if __name__ == "__main__":
    main()