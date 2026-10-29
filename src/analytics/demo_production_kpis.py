"""
Quick demo: print the 5 production KPIs for several slices.

⚠️ SYNTHETIC DATA — results shown are NOT real factory performance.

Usage:
    python -m src.analytics.demo_production_kpis
"""
from __future__ import annotations

from src.analytics.production_kpis import (
    KpiFilter,
    all_production_kpis,
)


def print_block(title: str, kpis: dict) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    ta = kpis["target_achievement"]
    v = kpis["variance"]
    e = kpis["efficiency"]
    p = kpis["productivity"]
    o = kpis["overtime"]

    print(f"  Rows             : {ta['n_rows']:,}")
    print(f"  Actual / Planned : {ta['actual_qty']:,} / {ta['planned_qty']:,}")
    print(f"  Achievement %    : {ta['achievement_pct']} %")
    print(f"  Variance         : {v['variance_pcs']:+,} pcs ({v['variance_sign']})")
    print(f"  Line efficiency  : {e['efficiency_pct']} %")
    print(f"  Productivity     : {p['productivity_pcs_per_hr']} pcs/worker-hr")
    print(f"  Overtime rate    : {o['overtime_rate_pct']} %")


def main() -> None:
    print("=" * 60)
    print("GFIS — Production KPI Demo")
    print("⚠️  SYNTHETIC DATA — not real factory performance")
    print("=" * 60)

    # 1. All data
    print_block("All production (Nov 2025 – Apr 2026)",
                all_production_kpis())

    # 2. Line LN-01
    print_block("Line LN-01 (all shifts)",
                all_production_kpis(KpiFilter(line_id="LN-01")))

    # 3. Shift A only
    print_block("Shift A (all lines)",
                all_production_kpis(KpiFilter(shift="A")))

    # 4. Last 30 days of the demo window
    print_block("March 2026 (2026-03-01 → 2026-03-31)",
                all_production_kpis(KpiFilter(
                    date_from="2026-03-01", date_to="2026-03-31")))

    print("\n" + "=" * 60)
    print("Demo complete.")


if __name__ == "__main__":
    main()