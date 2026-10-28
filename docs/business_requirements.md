# GFIS — Business Requirements Document v0.2

**Status:** Draft — locked end of Day 2
**Supersedes:** v0.1 (Day 0)

## 1. Purpose
Provide garments factory management with a single decision-support system covering
production, finance, quality, inventory, delivery, root-cause, and forecasting.

## 2. Users
Owner, Production Manager, Merchandiser, QC Manager, Finance, Store.

## 3. Business questions
Each maps to at least one table from `docs/data_dictionary.md`.

| # | Question | Tables used | KPI computed |
|---|---|---|---|
| Q1 | Are we hitting daily/weekly/monthly production targets? | production_daily, production_plan | target %, variance |
| Q2 | What is our profit, and which orders are unprofitable? | orders, expenses, sales_revenue, cost_standards | GP, NP, margin per order |
| Q3 | Where are we wasting money? | expenses, machine_downtime, inventory_transactions | overtime rate, downtime cost, wastage rate |
| Q4 | Why did production drop / cost rise / defects increase? | all | root-cause engine |
| Q5 | Which orders will be late? | orders, shipments, production_daily | delay-risk classifier |
| Q6 | What will we produce and earn next week/month? | production_daily, sales_revenue | forecast |
| Q7 | What actions should we take, and did they work? | corrective_actions + all | action tracker |

## 4. Scope — v1.0 (30-day sprint)

IN:
- 15 synthetic tables, validated
- Core KPI engine (production, financial, quality, inventory, order)
- Root-cause engine for 5 investigations
- Streamlit dashboard (~7 pages)
- Production + revenue forecast with baseline comparison
- Order-delay risk classifier
- Scenario analysis (cost/volume/what-if)
- Corrective action tracker
- Tests + GitHub Actions
- Docs: dictionary, KPI ref, model card, user guide, boss deck

OUT:
- LLM Q&A assistant
- OR-Tools scheduling
- Docker
- Real-time ingestion
- Authentication

## 5. Success criteria (v1.0)
- [ ] All 15 tables pass data-quality tests
- [ ] 20+ KPIs implemented and unit-tested
- [ ] Dashboard runs from README on a fresh venv
- [ ] 5 root-cause investigations with evidence trail
- [ ] Forecast + classifier beat naive baselines on held-out data
- [ ] Boss presentation explains problem → evidence → action → verified outcome
- [ ] Limitations documented

## 6. Data requirements
See `docs/data_dictionary.md` (v0.2). 15 tables, 9 ID prefixes,
12 enum domains, ~100 columns total.

## 7. Accounting policy (v1.0)
- Single currency: USD
- Revenue recognition: on `recognized_date` (not invoice, not cash)
- COGS: fabric + CM per shipment milestone
- Operating expense: everything not COGS
- Profit: GP = revenue − COGS; NP = GP − OpEx
- No tax, no depreciation, no FX in v1

## 8. Known risks
| Risk | Mitigation |
|---|---|
| Synthetic data unrealism | Document every assumption in `docs/data_dictionary.md` |
| Revenue vs cash confusion | Separate columns, separate KPIs, disclaimer on every chart |
| ML leakage | Chronological split, documented in model card |
| Scope creep | v1.0 feature list frozen end of Day 2 |

## 9. Acceptance of v0.2
- [ ] Data dictionary covers all 15 tables with columns, units, nullability
- [ ] ID conventions & enums locked in `config/constants.py`
- [ ] 10 data-quality rules written (become Day 6 tests)
- [ ] Accounting policy stated (revenue ≠ cash)
- [ ] BRD scope v1.0 finalized