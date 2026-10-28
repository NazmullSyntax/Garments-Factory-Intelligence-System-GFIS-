# GFIS — Data Dictionary (v0.2)

**Status:** Draft — locked after Day 2 review
**Author:** <your name>
**Date:** <today>

⚠️ All data in this project is **synthetic** unless explicitly stated otherwise.
Synthetic data is labeled in every chart, report, and dashboard page.

---

## ID Conventions

| ID | Format | Example | Cross-refs |
|---|---|---|---|
| order_id | `ORD-YYYY-NNNN` | ORD-2026-0042 | orders, sales_revenue, shipments, production_plan, production_daily |
| style_id | `STY-NNNN` | STY-0157 | orders, cost_standards, quality_inspection, production_daily |
| line_id | `LN-NN` | LN-04 | production_daily, labor_attendance, machine_downtime |
| buyer_id | `BUY-NN` | BUY-03 | orders |
| supplier_id | `SUP-NN` | SUP-07 | purchase_orders |
| material_id | `MAT-NNNN` | MAT-0092 | inventory_transactions, purchase_orders |
| machine_id | `MAC-NN` | MAC-11 | machine_downtime, maintenance |
| worker_id | `WRK-NNNN` | WRK-0234 | labor_attendance |

**Enums:**
- `shift`: A, B, C
- `department`: Cutting, Sewing, Finishing, Packing
- `order.status`: Open, InProduction, Shipped, Closed, Cancelled
- `expense.category`: Material, Labor, Electricity, Transport, Overtime, Overhead, Maintenance, Other
- `quality.defect_category`: Stitch, Measurement, Fabric, Stain, Trimming, Other
- `quality.defect_severity`: Minor, Major, Critical
- `downtime.reason_category`: Breakdown, Changeover, MaterialShortage, NoOperator, Power, Scheduled
- `inventory.transaction_type`: Opening, Receipt, Issue, Adjustment
- `inventory.material_type`: Fabric, Trims, Accessories
- `shipment.shipment_mode`: Sea, Air

**Units — always explicit in column name when ambiguous:**
- `*_qty` → pieces (pcs) unless noted
- `*_usd` → USD
- `*_hours` → hours
- `*_minutes` → minutes
- `*_meters` → meters
- `sam_per_unit` → minutes

---

## Tables (15)

### 1. production_daily
One row = line × shift × date × order.

| Column | Type | Unit | Null | Meaning |
|---|---|---|---|---|
| production_date | DATE | — | No | Date |
| line_id | VARCHAR | — | No | FK → line |
| shift | VARCHAR | — | No | A/B/C |
| order_id | VARCHAR | — | No | FK → orders |
| style_id | VARCHAR | — | No | FK → style |
| planned_qty | INT | pcs | No | Target for this line/shift |
| actual_qty | INT | pcs | No | Total produced |
| good_qty | INT | pcs | No | Passed QC (≤ actual) |
| reject_qty | INT | pcs | No | Rejected |
| manpower_used | INT | workers | No | Workers on the line |
| worked_hours | DECIMAL | hours | No | Total hours |
| sam_per_unit | DECIMAL | minutes | No | Standard allowed minutes |
| overtime_hours | DECIMAL | hours | Yes | Beyond shift |
| created_at | TIMESTAMP | — | No | Ingestion ts |

**KPIs:** target achievement %, production variance, line efficiency, labor productivity, overtime rate.

---

### 2. production_plan
What was planned (versioned).

| Column | Type | Unit | Null | Meaning |
|---|---|---|---|---|
| plan_date | DATE | — | No | Date covered |
| plan_version | VARCHAR | — | No | v1, v2, ... |
| line_id | VARCHAR | — | No | FK → line |
| shift | VARCHAR | — | No | A/B/C |
| order_id | VARCHAR | — | No | FK → orders |
| style_id | VARCHAR | — | No | FK → style |
| planned_qty | INT | pcs | No | Target |
| planned_manpower | INT | workers | No | Planned workers |
| planned_hours | DECIMAL | hours | No | Planned hours |
| approved_by | VARCHAR | — | No | Role |

---

### 3. orders
Buyer purchase orders (contracts).

| Column | Type | Unit | Null | Meaning |
|---|---|---|---|---|
| order_id | VARCHAR | — | No | PK |
| buyer_id | VARCHAR | — | No | FK → buyer |
| style_id | VARCHAR | — | No | FK → style |
| order_date | DATE | — | No | — |
| delivery_date | DATE | — | No | Contractual |
| order_qty | INT | pcs | No | — |
| unit_price_usd | DECIMAL | USD | No | FOB/pc |
| total_value_usd | DECIMAL | USD | No | qty × price |
| status | VARCHAR | — | No | Open/InProduction/Shipped/Closed/Cancelled |
| fabric_cost_usd | DECIMAL | USD | No | Est. fabric cost |
| cm_cost_usd | DECIMAL | USD | No | Cut & Make |
| payment_terms_days | INT | days | No | 30/60/90 |

---

### 4. sales_revenue
Revenue recognition events.

| Column | Type | Unit | Null | Meaning |
|---|---|---|---|---|
| revenue_id | VARCHAR | — | No | PK |
| order_id | VARCHAR | — | No | FK → orders |
| invoice_date | DATE | — | No | — |
| recognized_date | DATE | — | No | — |
| invoice_amount_usd | DECIMAL | USD | No | — |
| recognized_amount_usd | DECIMAL | USD | No | — |
| cash_received_usd | DECIMAL | USD | No | Actual cash (0 if unpaid) |
| cash_received_date | DATE | — | Yes | Nullable |
| currency | VARCHAR | — | No | USD (v1) |

**⚠️ Accounting rule:** invoice ≠ recognized ≠ cash. All three are separate columns.

---

### 5. expenses

| Column | Type | Unit | Null | Meaning |
|---|---|---|---|---|
| expense_id | VARCHAR | — | No | PK |
| expense_date | DATE | — | No | — |
| category | VARCHAR | — | No | see enum above |
| subcategory | VARCHAR | — | Yes | — |
| order_id | VARCHAR | — | Yes | Nullable |
| line_id | VARCHAR | — | Yes | Nullable |
| amount_usd | DECIMAL | USD | No | — |
| vendor | VARCHAR | — | Yes | — |
| payment_status | VARCHAR | — | No | Paid/Pending/Overdue |

---

### 6. labor_attendance
One row = worker × date × shift.

| Column | Type | Unit | Null | Meaning |
|---|---|---|---|---|
| attendance_date | DATE | — | No | — |
| worker_id | VARCHAR | — | No | FK → worker |
| line_id | VARCHAR | — | No | FK → line |
| shift | VARCHAR | — | No | A/B/C |
| department | VARCHAR | — | No | Cutting/Sewing/Finishing/Packing |
| present | BOOLEAN | — | No | — |
| hours_worked | DECIMAL | hours | No | — |
| overtime_hours | DECIMAL | hours | No | — |
| wage_rate_usd_per_hour | DECIMAL | USD/hr | No | — |
| total_wage_usd | DECIMAL | USD | No | — |

---

### 7. quality_inspection

| Column | Type | Unit | Null | Meaning |
|---|---|---|---|---|
| inspection_id | VARCHAR | — | No | PK |
| inspection_date | DATE | — | No | — |
| order_id | VARCHAR | — | No | FK → orders |
| style_id | VARCHAR | — | No | FK → style |
| line_id | VARCHAR | — | No | FK → line |
| shift | VARCHAR | — | No | A/B/C |
| inspection_stage | VARCHAR | — | No | InLine/EndLine/Final |
| inspected_qty | INT | pcs | No | — |
| defective_qty | INT | pcs | No | — |
| rework_qty | INT | pcs | No | — |
| rejected_qty | INT | pcs | No | — |
| defect_category | VARCHAR | — | No | see enum |
| defect_severity | VARCHAR | — | No | Minor/Major/Critical |

**Rule:** `defective_qty ≤ inspected_qty`; `rework + rejected ≤ defective` (some defects repaired in place).

---

### 8. machine_downtime

| Column | Type | Unit | Null | Meaning |
|---|---|---|---|---|
| downtime_id | VARCHAR | — | No | PK |
| machine_id | VARCHAR | — | No | FK → machine |
| line_id | VARCHAR | — | No | FK → line |
| start_time | TIMESTAMP | — | No | — |
| end_time | TIMESTAMP | — | No | — |
| duration_minutes | INT | minutes | No | Computed = end − start |
| reason_category | VARCHAR | — | No | see enum |
| shift | VARCHAR | — | No | A/B/C |
| production_impact_qty | INT | pcs | No | Est. loss |

---

### 9. inventory_transactions

| Column | Type | Unit | Null | Meaning |
|---|---|---|---|---|
| transaction_id | VARCHAR | — | No | PK |
| transaction_date | DATE | — | No | — |
| material_id | VARCHAR | — | No | FK → material |
| material_type | VARCHAR | — | No | Fabric/Trims/Accessories |
| transaction_type | VARCHAR | — | No | Opening/Receipt/Issue/Adjustment |
| quantity | DECIMAL | meters or pcs | No | Signed |
| unit_cost_usd | DECIMAL | USD/unit | No | — |
| total_cost_usd | DECIMAL | USD | No | — |
| order_id | VARCHAR | — | Yes | Nullable |
| reference_doc | VARCHAR | — | Yes | — |

**Balance rule:** closing = opening + receipts − issues ± adjustments (validate per material/day).

---

### 10. purchase_orders

| Column | Type | Unit | Null | Meaning |
|---|---|---|---|---|
| po_id | VARCHAR | — | No | PK |
| supplier_id | VARCHAR | — | No | FK → supplier |
| material_id | VARCHAR | — | No | FK → material |
| po_date | DATE | — | No | — |
| promised_date | DATE | — | No | — |
| actual_receipt_date | DATE | — | Yes | — |
| quantity | DECIMAL | — | No | — |
| unit_price_usd | DECIMAL | USD | No | — |
| total_cost_usd | DECIMAL | USD | No | — |
| status | VARCHAR | — | No | Open/Received/Partial/Cancelled |

---

### 11. cost_standards

| Column | Type | Unit | Null | Meaning |
|---|---|---|---|---|
| style_id | VARCHAR | — | No | PK |
| sam_per_unit | DECIMAL | minutes | No | — |
| standard_fabric_meters | DECIMAL | meters | No | — |
| standard_fabric_cost_usd | DECIMAL | USD | No | — |
| standard_cm_cost_usd | DECIMAL | USD | No | — |
| standard_unit_cost_usd | DECIMAL | USD | No | — |
| effective_from | DATE | — | No | — |

---

### 12. budget

| Column | Type | Unit | Null | Meaning |
|---|---|---|---|---|
| budget_month | DATE | — | No | First of month |
| category | VARCHAR | — | No | expense category |
| budgeted_amount_usd | DECIMAL | USD | No | — |
| notes | VARCHAR | — | Yes | — |

---

### 13. cash_flow

| Column | Type | Unit | Null | Meaning |
|---|---|---|---|---|
| cf_id | VARCHAR | — | No | PK |
| period_date | DATE | — | No | — |
| flow_type | VARCHAR | — | No | Inflow/Outflow |
| category | VARCHAR | — | No | — |
| amount_usd | DECIMAL | USD | No | Signed |
| reference | VARCHAR | — | Yes | — |

---

### 14. maintenance

| Column | Type | Unit | Null | Meaning |
|---|---|---|---|---|
| maintenance_id | VARCHAR | — | No | PK |
| machine_id | VARCHAR | — | No | FK → machine |
| maintenance_date | DATE | — | No | — |
| maintenance_type | VARCHAR | — | No | Preventive/Corrective/Emergency |
| duration_minutes | INT | minutes | No | — |
| cost_usd | DECIMAL | USD | No | — |
| technician | VARCHAR | — | Yes | — |
| notes | VARCHAR | — | Yes | — |

---

### 15. shipments

| Column | Type | Unit | Null | Meaning |
|---|---|---|---|---|
| shipment_id | VARCHAR | — | No | PK |
| order_id | VARCHAR | — | No | FK → orders |
| ship_date | DATE | — | No | — |
| promised_date | DATE | — | No | — |
| shipped_qty | INT | pcs | No | — |
| destination_country | VARCHAR | — | No | — |
| shipment_mode | VARCHAR | — | No | Sea/Air |
| on_time | BOOLEAN | — | No | ship ≤ promised |
| delay_days | INT | days | No | max(0, ship − promised) |

---

## Cross-table join map (the spine of every KPI)

    orders ─┬─ production_plan
            ├─ production_daily
            ├─ quality_inspection
            ├─ sales_revenue
            ├─ shipments
            └─ expenses (nullable order_id)

    line_id ─┬─ production_daily
             ├─ labor_attendance
             └─ machine_downtime

    style_id ─┬─ orders
              ├─ cost_standards
              └─ quality_inspection

    material_id ─┬─ inventory_transactions
                 └─ purchase_orders

    machine_id ─┬─ machine_downtime
                └─ maintenance

---

## Data-quality rules (v0.2 — enforced in Day 6 tests)

1. Primary keys are unique per table
2. Every FK has a valid parent row (referential integrity)
3. `good_qty + reject_qty = actual_qty` (±0 tolerance)
4. `defective_qty ≤ inspected_qty`
5. `on_time = (ship_date ≤ promised_date)`
6. `duration_minutes = end_time − start_time`
7. `total_wage_usd = hours_worked × wage_rate + overtime_hours × wage_rate × 1.5`
8. All `*_usd` ≥ 0 (no negative costs)
9. `production_date` within active order window
10. No future-dated rows beyond today

---

## Synthetic-data disclosure

All rows in `data/sample/` are **synthetic**. They are generated to be internally
consistent for demonstration and testing. They do **not** represent any real
factory, buyer, supplier, or worker. Any analysis output derived from them
must be labeled **"Synthetic demo data"** in reports and dashboards.
'@ | Out-File -Encoding utf8 docs/data_dictionary.md