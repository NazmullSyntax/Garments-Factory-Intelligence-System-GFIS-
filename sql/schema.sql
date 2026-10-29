-- GFIS — schema.sql
-- Canonical table definitions for the GFIS DuckDB database.
-- v0.1-day5
--
-- ⚠️ SYNTHETIC DATA — every table in this database is synthetic.
--    See docs/data_dictionary.md for column meanings.

-- ============================================================
-- Master data (Day 3)
-- ============================================================

CREATE TABLE IF NOT EXISTS buyers (
    buyer_id            VARCHAR PRIMARY KEY,
    buyer_name          VARCHAR NOT NULL,
    country             VARCHAR NOT NULL,
    payment_terms_days  INTEGER NOT NULL,
    created_at          VARCHAR
);

CREATE TABLE IF NOT EXISTS styles (
    style_id                     VARCHAR PRIMARY KEY,
    style_name                   VARCHAR NOT NULL,
    product_type                 VARCHAR NOT NULL,
    sam_per_unit                 DOUBLE NOT NULL,
    standard_fabric_meters       DOUBLE NOT NULL,
    standard_fabric_cost_usd     DOUBLE NOT NULL,
    standard_cm_cost_usd         DOUBLE NOT NULL,
    standard_unit_cost_usd       DOUBLE NOT NULL,
    target_selling_price_usd     DOUBLE NOT NULL,
    effective_from               DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS cost_standards (
    style_id                     VARCHAR PRIMARY KEY,
    sam_per_unit                 DOUBLE NOT NULL,
    standard_fabric_meters       DOUBLE NOT NULL,
    standard_fabric_cost_usd     DOUBLE NOT NULL,
    standard_cm_cost_usd         DOUBLE NOT NULL,
    standard_unit_cost_usd       DOUBLE NOT NULL,
    effective_from               DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id             VARCHAR PRIMARY KEY,
    buyer_id             VARCHAR NOT NULL,
    style_id             VARCHAR NOT NULL,
    order_date           DATE NOT NULL,
    delivery_date        DATE NOT NULL,
    order_qty            INTEGER NOT NULL,
    unit_price_usd       DOUBLE NOT NULL,
    total_value_usd      DOUBLE NOT NULL,
    status               VARCHAR NOT NULL,
    fabric_cost_usd      DOUBLE NOT NULL,
    cm_cost_usd          DOUBLE NOT NULL,
    payment_terms_days   INTEGER NOT NULL,
    delivery_risk_flag   BOOLEAN,
    margin_squeeze_flag  BOOLEAN
);

-- ============================================================
-- Transactional data (Day 4)
-- ============================================================

CREATE TABLE IF NOT EXISTS production_plan (
    plan_date         DATE NOT NULL,
    plan_version      VARCHAR NOT NULL,
    line_id           VARCHAR NOT NULL,
    shift             VARCHAR NOT NULL,
    order_id          VARCHAR NOT NULL,
    style_id          VARCHAR NOT NULL,
    planned_qty       INTEGER NOT NULL,
    planned_manpower  INTEGER NOT NULL,
    planned_hours     DOUBLE NOT NULL,
    approved_by       VARCHAR
);

CREATE TABLE IF NOT EXISTS production_daily (
    production_date  DATE NOT NULL,
    line_id          VARCHAR NOT NULL,
    shift            VARCHAR NOT NULL,
    order_id         VARCHAR NOT NULL,
    style_id         VARCHAR NOT NULL,
    planned_qty      INTEGER NOT NULL,
    actual_qty       INTEGER NOT NULL,
    good_qty         INTEGER NOT NULL,
    reject_qty       INTEGER NOT NULL,
    manpower_used    INTEGER NOT NULL,
    worked_hours     DOUBLE NOT NULL,
    sam_per_unit     DOUBLE NOT NULL,
    overtime_hours   DOUBLE,
    created_at       VARCHAR
);

CREATE TABLE IF NOT EXISTS labor_attendance (
    attendance_date        DATE NOT NULL,
    worker_id              VARCHAR NOT NULL,
    line_id                VARCHAR NOT NULL,
    shift                  VARCHAR NOT NULL,
    department             VARCHAR NOT NULL,
    present                BOOLEAN NOT NULL,
    hours_worked           DOUBLE NOT NULL,
    overtime_hours         DOUBLE NOT NULL,
    wage_rate_usd_per_hour DOUBLE NOT NULL,
    total_wage_usd         DOUBLE NOT NULL
);

CREATE TABLE IF NOT EXISTS quality_inspection (
    inspection_id     VARCHAR PRIMARY KEY,
    inspection_date   DATE NOT NULL,
    order_id          VARCHAR NOT NULL,
    style_id          VARCHAR NOT NULL,
    line_id           VARCHAR NOT NULL,
    shift             VARCHAR NOT NULL,
    inspection_stage  VARCHAR NOT NULL,
    inspected_qty     INTEGER NOT NULL,
    defective_qty     INTEGER NOT NULL,
    rework_qty        INTEGER NOT NULL,
    rejected_qty      INTEGER NOT NULL,
    defect_category   VARCHAR NOT NULL,
    defect_severity   VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS machine_downtime (
    downtime_id            VARCHAR PRIMARY KEY,
    machine_id             VARCHAR NOT NULL,
    line_id                VARCHAR NOT NULL,
    start_time             TIMESTAMP NOT NULL,
    end_time               TIMESTAMP NOT NULL,
    duration_minutes       INTEGER NOT NULL,
    reason_category        VARCHAR NOT NULL,
    shift                  VARCHAR NOT NULL,
    production_impact_qty  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS maintenance (
    maintenance_id    VARCHAR PRIMARY KEY,
    machine_id        VARCHAR NOT NULL,
    maintenance_date  DATE NOT NULL,
    maintenance_type  VARCHAR NOT NULL,
    duration_minutes  INTEGER NOT NULL,
    cost_usd          DOUBLE NOT NULL,
    technician        VARCHAR,
    notes             VARCHAR
);

CREATE TABLE IF NOT EXISTS inventory_transactions (
    transaction_id    VARCHAR PRIMARY KEY,
    transaction_date  DATE NOT NULL,
    material_id       VARCHAR NOT NULL,
    material_type     VARCHAR NOT NULL,
    transaction_type  VARCHAR NOT NULL,
    quantity          DOUBLE NOT NULL,
    unit_cost_usd     DOUBLE NOT NULL,
    total_cost_usd    DOUBLE NOT NULL,
    order_id          VARCHAR,
    reference_doc     VARCHAR
);

CREATE TABLE IF NOT EXISTS purchase_orders (
    po_id                 VARCHAR PRIMARY KEY,
    supplier_id           VARCHAR NOT NULL,
    material_id           VARCHAR NOT NULL,
    po_date               DATE NOT NULL,
    promised_date         DATE NOT NULL,
    actual_receipt_date   DATE,
    quantity              DOUBLE NOT NULL,
    unit_price_usd        DOUBLE NOT NULL,
    total_cost_usd        DOUBLE NOT NULL,
    status                VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS expenses (
    expense_id      VARCHAR PRIMARY KEY,
    expense_date    DATE NOT NULL,
    category        VARCHAR NOT NULL,
    subcategory     VARCHAR,
    order_id        VARCHAR,
    line_id         VARCHAR,
    amount_usd      DOUBLE NOT NULL,
    vendor          VARCHAR,
    payment_status  VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS sales_revenue (
    revenue_id             VARCHAR PRIMARY KEY,
    order_id               VARCHAR NOT NULL,
    invoice_date           DATE NOT NULL,
    recognized_date        DATE NOT NULL,
    invoice_amount_usd     DOUBLE NOT NULL,
    recognized_amount_usd  DOUBLE NOT NULL,
    cash_received_usd      DOUBLE NOT NULL,
    cash_received_date     DATE,
    currency               VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS cash_flow (
    cf_id         VARCHAR PRIMARY KEY,
    period_date   DATE NOT NULL,
    flow_type     VARCHAR NOT NULL,
    category      VARCHAR NOT NULL,
    amount_usd    DOUBLE NOT NULL,
    reference     VARCHAR
);

CREATE TABLE IF NOT EXISTS budget (
    budget_month          DATE NOT NULL,
    category              VARCHAR NOT NULL,
    budgeted_amount_usd   DOUBLE NOT NULL,
    notes                 VARCHAR
);

CREATE TABLE IF NOT EXISTS shipments (
    shipment_id          VARCHAR PRIMARY KEY,
    order_id             VARCHAR NOT NULL,
    ship_date            DATE NOT NULL,
    promised_date        DATE NOT NULL,
    shipped_qty          INTEGER NOT NULL,
    destination_country  VARCHAR NOT NULL,
    shipment_mode        VARCHAR NOT NULL,
    on_time              BOOLEAN NOT NULL,
    delay_days           INTEGER NOT NULL
);