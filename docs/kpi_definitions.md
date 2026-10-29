# GFIS — KPI Definitions (v0.1 — Production)

**Status:** Draft — locked after Day 7 review
**Date:** Day 7 of 30-day sprint

⚠️ All data underlying these KPIs is **synthetic**. See README.

---

## 1. Target Achievement %

**Business meaning:** Are we hitting the plan? The single number that tells management
whether the factory delivered what it promised to deliver.

**Formula:**


**Numerator:** total pieces actually produced (includes rejects — the plan asked for pieces, not good pieces).
**Denominator:** total pieces planned.

**Worked example:**
3 days on LN-01, planned 500+500+500 = 1500; actual 480+510+460 = 1450.
→ `(1450 / 1500) × 100 = 96.67 %`

**Thresholds:**
- ≥ 95 % healthy
- 90 – 95 % watch
- < 90 % escalation

**Common mistakes:**
- Averaging daily percentages. Always **sum raw quantities first**.
- Using `good_qty` instead of `actual_qty`. Plan counts what was made, not what passed.

**Limitations:**
- Cannot distinguish "line was shut down" from "line was slow". Pair with KPI 5 (OT)
  and downtime data to diagnose.

---

## 2. Production Variance (pcs)

**Business meaning:** The size of the shortfall in pieces. Percentages hide scale —
−2 % of 100 000 is 2 000 pcs, worth chasing; −2 % of 500 is 10 pcs, ignore.

**Formula:**


**Worked example:** `1450 − 1500 = −50 pcs` (shortfall).

**Interpretation:**
- Negative = shortfall (recover or escalate).
- Positive = overproduction (may indicate plan too conservative).
- Zero = exactly on plan (rare; suspicious if recurring).

**Common mistakes:** confusing sign. Negative means **under**-plan.

---

## 3. Line Efficiency % (SAM-based)

**Business meaning:** Of the labor minutes actually spent, how many were
"standard minutes" of work actually produced? A 65 % efficiency means
35 % of the labor hour didn't translate into standard work — waiting, rework,
walking, or finding materials.

**Formula:**