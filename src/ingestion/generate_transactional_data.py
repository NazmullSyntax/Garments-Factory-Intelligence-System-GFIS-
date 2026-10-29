"""
GFIS — Day 4 synthetic transactional data generator.

Reads Day 3 master data (buyers, styles, orders, cost_standards) and
generates 13 transactional CSVs into data/sample/.

Reproducible: fixed SEED means same files on every run.

⚠️ SYNTHETIC DATA — no real production, quality, or financial results.
"""
from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

# --- Config ---
SEED = 42
random.seed(SEED)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE = PROJECT_ROOT / "data" / "sample"
SAMPLE.mkdir(parents=True, exist_ok=True)

DEMO_START = date(2025, 11, 1)
DEMO_END = date(2026, 4, 30)

# Factory layout
LINES = [f"LN-{i:02d}" for i in range(1, 9)]      # 8 sewing lines
MACHINES_PER_LINE = 3
SHIFTS = ["A", "B", "C"]
WORKERS_PER_LINE = 40
WAGE_RATE_RANGE = (0.55, 0.95)                    # USD/hour

# Product "pieces per minute per line" (rough factory throughput)
# Lower for complex styles (denim jacket), higher for simple (tee)
THROUGHPUT = {
    "Basic Tee":     8.0,
    "Polo Shirt":    5.5,
    "Denim Jeans":   2.5,
    "Denim Jacket":  1.8,
    "Hoodie":        3.0,
    "Kids Tee":      9.0,
}

# --- Load Day 3 master data ---
print("Loading Day 3 master data...")
buyers = pd.read_csv(SAMPLE / "buyers.csv")
styles = pd.read_csv(SAMPLE / "styles.csv")
orders = pd.read_csv(SAMPLE / "orders.csv")
cost_standards = pd.read_csv(SAMPLE / "cost_standards.csv")

# Parse dates
orders["order_date"] = pd.to_datetime(orders["order_date"]).dt.date
orders["delivery_date"] = pd.to_datetime(orders["delivery_date"]).dt.date

# Style lookup
style_lookup = styles.set_index("style_id").to_dict("index")
order_lookup = orders.set_index("order_id").to_dict("index")

# Filter orders that were actually produced (not Open/Cancelled at end)
active_orders = orders[orders["status"].isin(
    ["InProduction", "Shipped", "Closed"])].copy()
print(f"Active orders for production: {len(active_orders)}")

ok = 0

# ============================================================
# 1 & 2. production_plan + production_daily
# ============================================================
print("Generating production_plan and production_daily...")
plan_rows = []
prod_rows = []

for _, order in active_orders.iterrows():
    oid = order["order_id"]
    sid = order["style_id"]
    qty = int(order["order_qty"])
    start = order["order_date"]
    end = order["delivery_date"]
    style_info = style_lookup[sid]
    sam = style_info["sam_per_unit"]
    ptype = style_info["product_type"]

    # Production window: start 3 days after order, end 5 days before delivery
    prod_start = start + timedelta(days=3)
    prod_end = end - timedelta(days=5)
    if prod_end <= prod_start:
        prod_end = prod_start + timedelta(days=15)
    days = (prod_end - prod_start).days
    if days <= 0:
        days = 10

    # Pick 1-2 lines per order
    n_lines = random.choice([1, 1, 2])
    lines_for_order = random.sample(LINES, n_lines)

    # Distribute qty across lines
    per_line = qty // len(lines_for_order)

    for line_id in lines_for_order:
        throughput = THROUGHPUT.get(ptype, 4.0)
        # Rough daily capacity: throughput * workers_effectiveness * hours
        # Assume 8 hours, 80% utilization
        daily_capacity = int(throughput * 8 * 0.8 * random.uniform(0.9, 1.1))
        if daily_capacity <= 0:
            daily_capacity = 200
        n_days_needed = max(1, per_line // daily_capacity)
        if n_days_needed > days:
            n_days_needed = days

        daily_qty = per_line // max(1, n_days_needed)

        for d in range(n_days_needed):
            prod_date = prod_start + timedelta(
                days=int(d * (days / max(1, n_days_needed))))

            if prod_date > DEMO_END:
                continue

            shift = "A"  # simplify: one shift per line-day for v1

            planned = daily_qty
            # Business scenarios: 15% shortfall, 5% overperformance
            r = random.random()
            if r < 0.15:
                actual = int(planned * random.uniform(0.70, 0.95))
            elif r < 0.20:
                actual = int(planned * random.uniform(1.00, 1.10))
            else:
                actual = int(planned * random.uniform(0.93, 1.02))

            # Quality: 2-8% reject
            reject_rate = random.uniform(0.02, 0.08)
            reject = int(actual * reject_rate)
            good = actual - reject

            manpower = WORKERS_PER_LINE + random.randint(-3, 3)
            worked_h = 8.0 + random.choice([0, 0, 0, 1, 2])
            overtime = max(0.0, worked_h - 8.0)

            plan_rows.append({
                "plan_date": prod_date,
                "plan_version": "v1",
                "line_id": line_id,
                "shift": shift,
                "order_id": oid,
                "style_id": sid,
                "planned_qty": planned,
                "planned_manpower": WORKERS_PER_LINE,
                "planned_hours": 8.0,
                "approved_by": "Production Manager",
            })

            prod_rows.append({
                "production_date": prod_date,
                "line_id": line_id,
                "shift": shift,
                "order_id": oid,
                "style_id": sid,
                "planned_qty": planned,
                "actual_qty": actual,
                "good_qty": good,
                "reject_qty": reject,
                "manpower_used": manpower,
                "worked_hours": worked_h,
                "sam_per_unit": sam,
                "overtime_hours": overtime,
                "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            })

plan_df = pd.DataFrame(plan_rows)
prod_df = pd.DataFrame(prod_rows)
plan_df.to_csv(SAMPLE / "production_plan.csv", index=False)
prod_df.to_csv(SAMPLE / "production_daily.csv", index=False)
print(f"[OK] production_plan.csv     {len(plan_df):>5} rows")
print(f"[OK] production_daily.csv    {len(prod_df):>5} rows")

# ============================================================
# 3. labor_attendance
# ============================================================
print("Generating labor_attendance...")
att_rows = []
worker_counter = 1
worker_map = {}  # line -> list of worker_ids

for line in LINES:
    worker_map[line] = []
    for _ in range(WORKERS_PER_LINE):
        wid = f"WRK-{worker_counter:04d}"
        worker_map[line].append(wid)
        worker_counter += 1

# One row per worker per production day
prod_dates = sorted(prod_df["production_date"].unique())

for line_id in LINES:
    for wid in worker_map[line_id]:
        wage_rate = round(random.uniform(*WAGE_RATE_RANGE), 2)
        for pdate in prod_dates:
            # 95% attendance
            present = random.random() < 0.95
            hours = 8.0 if present else 0.0
            ot = 0.0
            if present and random.random() < 0.20:
                ot = random.choice([1.0, 2.0, 3.0])
            att_rows.append({
                "attendance_date": pdate,
                "worker_id": wid,
                "line_id": line_id,
                "shift": "A",
                "department": "Sewing",
                "present": present,
                "hours_worked": hours,
                "overtime_hours": ot,
                "wage_rate_usd_per_hour": wage_rate,
                "total_wage_usd": round(hours * wage_rate + ot * wage_rate * 1.5, 2),
            })

att_df = pd.DataFrame(att_rows)
att_df.to_csv(SAMPLE / "labor_attendance.csv", index=False)
print(f"[OK] labor_attendance.csv    {len(att_df):>5} rows")

# ============================================================
# 4. quality_inspection
# ============================================================
print("Generating quality_inspection...")
defect_cats = ["Stitch", "Measurement", "Fabric", "Stain", "Trimming", "Other"]
defect_weights = [0.35, 0.25, 0.15, 0.10, 0.10, 0.05]

qc_rows = []
inspection_id = 1
for _, prod in prod_df.iterrows():
    if prod["actual_qty"] < 50:
        continue
    inspected = int(prod["actual_qty"] * random.uniform(0.90, 1.00))
    defect_rate = random.uniform(0.02, 0.10)
    defective = int(inspected * defect_rate)
    rework = int(defective * random.uniform(0.6, 0.9))
    rejected = defective - rework
    cat = random.choices(defect_cats, weights=defect_weights, k=1)[0]
    severity = random.choices(
        ["Minor", "Major", "Critical"], weights=[0.6, 0.3, 0.1], k=1)[0]
    stage = random.choices(
        ["InLine", "EndLine", "Final"], weights=[0.3, 0.5, 0.2], k=1)[0]

    qc_rows.append({
        "inspection_id": f"QC-{inspection_id:06d}",
        "inspection_date": prod["production_date"],
        "order_id": prod["order_id"],
        "style_id": prod["style_id"],
        "line_id": prod["line_id"],
        "shift": prod["shift"],
        "inspection_stage": stage,
        "inspected_qty": inspected,
        "defective_qty": defective,
        "rework_qty": rework,
        "rejected_qty": rejected,
        "defect_category": cat,
        "defect_severity": severity,
    })
    inspection_id += 1

qc_df = pd.DataFrame(qc_rows)
qc_df.to_csv(SAMPLE / "quality_inspection.csv", index=False)
print(f"[OK] quality_inspection.csv  {len(qc_df):>5} rows")

# ============================================================
# 5 & 6. machine_downtime + maintenance
# ============================================================
print("Generating machine_downtime and maintenance...")
machine_ids = []
for line in LINES:
    for m in range(1, MACHINES_PER_LINE + 1):
        machine_ids.append(f"MAC-{line[-2:]}{m:02d}")

downtime_reasons = ["Breakdown", "Changeover", "MaterialShortage",
                    "NoOperator", "Power", "Scheduled"]
reason_weights = [0.30, 0.25, 0.15, 0.10, 0.10, 0.10]

dt_rows = []
dt_id = 1
for pdate in prod_dates:
    for mac in machine_ids:
        # 25% chance of one downtime event per machine per day
        if random.random() < 0.25:
            start_hour = random.randint(0, 6)
            duration = random.choice([5, 10, 15, 20, 30, 45, 60, 120])
            start_dt = datetime.combine(pdate, datetime.min.time()) + timedelta(hours=start_hour)
            end_dt = start_dt + timedelta(minutes=duration)
            reason = random.choices(downtime_reasons, weights=reason_weights, k=1)[0]
            line_id = "LN-" + mac[4:6]
            dt_rows.append({
                "downtime_id": f"DT-{dt_id:06d}",
                "machine_id": mac,
                "line_id": line_id,
                "start_time": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_minutes": duration,
                "reason_category": reason,
                "shift": "A",
                "production_impact_qty": duration * random.randint(1, 4),
            })
            dt_id += 1

dt_df = pd.DataFrame(dt_rows)
dt_df.to_csv(SAMPLE / "machine_downtime.csv", index=False)
print(f"[OK] machine_downtime.csv    {len(dt_df):>5} rows")

maint_rows = []
mt_id = 1
for mac in machine_ids:
    n_events = random.randint(5, 10)
    for _ in range(n_events):
        mdate = DEMO_START + timedelta(days=random.randint(0, 180))
        mtype = random.choices(
            ["Preventive", "Corrective", "Emergency"],
            weights=[0.6, 0.3, 0.1], k=1)[0]
        maint_rows.append({
            "maintenance_id": f"MT-{mt_id:05d}",
            "machine_id": mac,
            "maintenance_date": mdate,
            "maintenance_type": mtype,
            "duration_minutes": random.choice([30, 45, 60, 90, 120, 180]),
            "cost_usd": round(random.uniform(20, 300), 2),
            "technician": f"TECH-{random.randint(1, 5):02d}",
            "notes": f"{mtype} maintenance",
        })
        mt_id += 1

mt_df = pd.DataFrame(maint_rows)
mt_df.to_csv(SAMPLE / "maintenance.csv", index=False)
print(f"[OK] maintenance.csv         {len(mt_df):>5} rows")

# ============================================================
# 7 & 8. inventory_transactions + purchase_orders
# ============================================================
print("Generating inventory_transactions and purchase_orders...")
materials = []
mat_counter = 1
# One fabric material per style + 5 trims
for sid in styles["style_id"].unique():
    materials.append({
        "material_id": f"MAT-{mat_counter:04d}",
        "material_type": "Fabric",
        "unit": "meters",
        "unit_cost": random.uniform(2.5, 6.0),
        "style_id": sid,
    })
    mat_counter += 1

trim_types = ["Buttons", "Zippers", "Thread", "Labels", "Polybags"]
for t in trim_types:
    materials.append({
        "material_id": f"MAT-{mat_counter:04d}",
        "material_type": "Trims",
        "unit": "pcs",
        "unit_cost": random.uniform(0.02, 0.50),
        "style_id": None,
    })
    mat_counter += 1

inv_rows = []
inv_id = 1
# Opening stock for each material at DEMO_START
for mat in materials:
    opening_qty = random.randint(1000, 5000) if mat["material_type"] == "Fabric" else random.randint(10000, 50000)
    inv_rows.append({
        "transaction_id": f"INV-{inv_id:06d}",
        "transaction_date": DEMO_START,
        "material_id": mat["material_id"],
        "material_type": mat["material_type"],
        "transaction_type": "Opening",
        "quantity": opening_qty,
        "unit_cost_usd": round(mat["unit_cost"], 2),
        "total_cost_usd": round(opening_qty * mat["unit_cost"], 2),
        "order_id": None,
        "reference_doc": "OPENING-2025-11",
    })
    inv_id += 1

# Receipts and issues during the demo window
for _ in range(2000):
    txn_date = DEMO_START + timedelta(days=random.randint(0, 180))
    mat = random.choice(materials)
    if random.random() < 0.5:
        # Receipt
        qty = random.randint(500, 3000) if mat["material_type"] == "Fabric" else random.randint(5000, 20000)
        ttype = "Receipt"
    else:
        # Issue
        qty = -random.randint(200, 1500) if mat["material_type"] == "Fabric" else -random.randint(1000, 8000)
        ttype = "Issue"

    inv_rows.append({
        "transaction_id": f"INV-{inv_id:06d}",
        "transaction_date": txn_date,
        "material_id": mat["material_id"],
        "material_type": mat["material_type"],
        "transaction_type": ttype,
        "quantity": qty,
        "unit_cost_usd": round(mat["unit_cost"], 2),
        "total_cost_usd": round(abs(qty) * mat["unit_cost"], 2),
        "order_id": None,
        "reference_doc": f"{ttype}-{inv_id:04d}",
    })
    inv_id += 1

inv_df = pd.DataFrame(inv_rows)
inv_df.to_csv(SAMPLE / "inventory_transactions.csv", index=False)
print(f"[OK] inventory_transactions.csv {len(inv_df):>4} rows")

# Purchase orders
suppliers = [f"SUP-{i:02d}" for i in range(1, 11)]
po_rows = []
po_id = 1
for mat in materials:
    n_pos = random.randint(2, 4)
    for _ in range(n_pos):
        po_date = DEMO_START + timedelta(days=random.randint(0, 150))
        promised = po_date + timedelta(days=random.randint(7, 30))
        # 20% late receipts
        if random.random() < 0.20:
            actual_receipt = promised + timedelta(days=random.randint(3, 15))
            status = "Received"
        elif random.random() < 0.15:
            actual_receipt = None
            status = "Open"
        else:
            actual_receipt = promised + timedelta(days=random.randint(-3, 3))
            status = "Received"

        qty = random.randint(500, 5000)
        unit_price = round(mat["unit_cost"] * random.uniform(0.95, 1.15), 2)

        po_rows.append({
            "po_id": f"PO-{po_id:05d}",
            "supplier_id": random.choice(suppliers),
            "material_id": mat["material_id"],
            "po_date": po_date,
            "promised_date": promised,
            "actual_receipt_date": actual_receipt,
            "quantity": qty,
            "unit_price_usd": unit_price,
            "total_cost_usd": round(qty * unit_price, 2),
            "status": status,
        })
        po_id += 1

po_df = pd.DataFrame(po_rows)
po_df.to_csv(SAMPLE / "purchase_orders.csv", index=False)
print(f"[OK] purchase_orders.csv     {len(po_df):>5} rows")

# ============================================================
# 9. expenses
# ============================================================
print("Generating expenses...")
exp_rows = []
exp_id = 1
exp_cats = ["Material", "Labor", "Electricity", "Transport",
            "Overtime", "Overhead", "Maintenance", "Other"]
cat_weights = [0.35, 0.25, 0.10, 0.08, 0.10, 0.07, 0.03, 0.02]

for _, prod in prod_df.iterrows():
    # Material expense (fabric consumed for this production)
    style_info = style_lookup[prod["style_id"]]
    fabric_m = style_info["standard_fabric_meters"] * prod["actual_qty"]
    material_cost = round(fabric_m * style_info["standard_fabric_cost_usd"] /
                          max(0.01, style_info["standard_fabric_meters"]) * 0.95, 2)
    exp_rows.append({
        "expense_id": f"EXP-{exp_id:06d}",
        "expense_date": prod["production_date"],
        "category": "Material",
        "subcategory": "Fabric",
        "order_id": prod["order_id"],
        "line_id": prod["line_id"],
        "amount_usd": material_cost,
        "vendor": "SUP-MAT",
        "payment_status": random.choice(["Paid", "Pending"]),
    })
    exp_id += 1

# Monthly overhead + utilities
for month_offset in range(6):
    mdate = date(2025, 11, 1) + pd.DateOffset(months=month_offset)
    for cat in ["Electricity", "Transport", "Overhead"]:
        exp_rows.append({
            "expense_id": f"EXP-{exp_id:06d}",
            "expense_date": mdate.date() if hasattr(mdate, 'date') else mdate,
            "category": cat,
            "subcategory": f"{cat} monthly",
            "order_id": None,
            "line_id": None,
            "amount_usd": round(random.uniform(2000, 15000), 2),
            "vendor": "UTILITY",
            "payment_status": "Paid",
        })
        exp_id += 1

exp_df = pd.DataFrame(exp_rows)
exp_df.to_csv(SAMPLE / "expenses.csv", index=False)
print(f"[OK] expenses.csv            {len(exp_df):>5} rows")

# ============================================================
# 10. sales_revenue
# ============================================================
print("Generating sales_revenue...")
rev_rows = []
rev_id = 1
for _, order in orders.iterrows():
    if order["status"] not in ["Shipped", "Closed"]:
        continue
    invoice_date = order["delivery_date"] + timedelta(days=random.randint(0, 5))
    recognized = invoice_date + timedelta(days=random.randint(0, 3))
    total = order["total_value_usd"]
    invoice_amt = total
    recognized_amt = total

    # 40% cash received, 60% pending
    if random.random() < 0.40:
        cash = total
        cash_date = recognized + timedelta(days=random.randint(5, 45))
    else:
        cash = 0.0
        cash_date = None

    rev_rows.append({
        "revenue_id": f"REV-{rev_id:05d}",
        "order_id": order["order_id"],
        "invoice_date": invoice_date,
        "recognized_date": recognized,
        "invoice_amount_usd": round(invoice_amt, 2),
        "recognized_amount_usd": round(recognized_amt, 2),
        "cash_received_usd": round(cash, 2),
        "cash_received_date": cash_date,
        "currency": "USD",
    })
    rev_id += 1

rev_df = pd.DataFrame(rev_rows)
rev_df.to_csv(SAMPLE / "sales_revenue.csv", index=False)
print(f"[OK] sales_revenue.csv       {len(rev_df):>5} rows")

# ============================================================
# 11. cash_flow
# ============================================================
print("Generating cash_flow...")
cf_rows = []
cf_id = 1
# Inflows from customer collections
for _, rev in rev_df.iterrows():
    if rev["cash_received_usd"] > 0 and pd.notna(rev["cash_received_date"]):
        cf_rows.append({
            "cf_id": f"CF-{cf_id:06d}",
            "period_date": rev["cash_received_date"],
            "flow_type": "Inflow",
            "category": "CustomerCollection",
            "amount_usd": rev["cash_received_usd"],
            "reference": rev["order_id"],
        })
        cf_id += 1

# Outflows — sample from expenses
for _, exp in exp_df.sample(min(200, len(exp_df)), random_state=1).iterrows():
    cf_rows.append({
        "cf_id": f"CF-{cf_id:06d}",
        "period_date": exp["expense_date"],
        "flow_type": "Outflow",
        "category": exp["category"],
        "amount_usd": -exp["amount_usd"],
        "reference": exp["expense_id"],
    })
    cf_id += 1

cf_df = pd.DataFrame(cf_rows)
cf_df.to_csv(SAMPLE / "cash_flow.csv", index=False)
print(f"[OK] cash_flow.csv           {len(cf_df):>5} rows")

# ============================================================
# 12. budget
# ============================================================
print("Generating budget...")
budget_rows = []
for month_offset in range(6):
    month_start = date(2025, 11, 1)
    # advance months
    y = month_start.year + (month_start.month - 1 + month_offset) // 12
    m = ((month_start.month - 1 + month_offset) % 12) + 1
    bm = date(y, m, 1)
    for cat in ["Material", "Labor", "Electricity", "Transport",
                "Overtime", "Overhead", "Maintenance"]:
        budget_rows.append({
            "budget_month": bm,
            "category": cat,
            "budgeted_amount_usd": round(random.uniform(5000, 50000), 2),
            "notes": f"Budget for {cat} — {bm.strftime('%B %Y')}",
        })

budget_df = pd.DataFrame(budget_rows)
budget_df.to_csv(SAMPLE / "budget.csv", index=False)
print(f"[OK] budget.csv              {len(budget_df):>5} rows")

# ============================================================
# 13. shipments
# ============================================================
print("Generating shipments...")
shp_rows = []
shp_id = 1
for _, order in orders.iterrows():
    if order["status"] not in ["Shipped", "Closed"]:
        continue
    promised = order["delivery_date"]
    # 25% late
    if random.random() < 0.25:
        delay = random.randint(2, 15)
    else:
        delay = random.randint(-3, 2)
    ship_date = promised + timedelta(days=delay)
    on_time = ship_date <= promised
    delay_days = max(0, (ship_date - promised).days)

    shp_rows.append({
        "shipment_id": f"SHP-{shp_id:05d}",
        "order_id": order["order_id"],
        "ship_date": ship_date,
        "promised_date": promised,
        "shipped_qty": order["order_qty"],
        "destination_country": buyers.loc[
            buyers["buyer_id"] == order["buyer_id"], "country"].iloc[0],
        "shipment_mode": random.choice(["Sea", "Air"]),
        "on_time": on_time,
        "delay_days": delay_days,
    })
    shp_id += 1

shp_df = pd.DataFrame(shp_rows)
shp_df.to_csv(SAMPLE / "shipments.csv", index=False)
print(f"[OK] shipments.csv           {len(shp_df):>5} rows")

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 55)
print("Day 4 generation complete.")
print("=" * 55)
print(f"production_plan          {len(plan_df):>6}")
print(f"production_daily         {len(prod_df):>6}")
print(f"labor_attendance         {len(att_df):>6}")
print(f"quality_inspection       {len(qc_df):>6}")
print(f"machine_downtime         {len(dt_df):>6}")
print(f"maintenance              {len(mt_df):>6}")
print(f"inventory_transactions   {len(inv_df):>6}")
print(f"purchase_orders          {len(po_df):>6}")
print(f"expenses                 {len(exp_df):>6}")
print(f"sales_revenue            {len(rev_df):>6}")
print(f"cash_flow                {len(cf_df):>6}")
print(f"budget                   {len(budget_df):>6}")
print(f"shipments                {len(shp_df):>6}")
print("=" * 55)