"""Day 2 status check. Run: python check_day2.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ok = 0
fail = 0


def check(label, condition, detail=""):
    global ok, fail
    if condition:
        print(f"[PASS] {label}" + (f" — {detail}" if detail else ""))
        ok += 1
    else:
        print(f"[FAIL] {label}" + (f" — {detail}" if detail else ""))
        fail += 1


print("\n=== GFIS Day 2 Status Check ===\n")

# --- 1. constants.py exists and is clean ---
const_path = ROOT / "config" / "constants.py"
if const_path.exists():
    first_line = const_path.read_text(encoding="utf-8").splitlines()[0]
    check(
        "constants.py first line is a docstring",
        first_line.startswith('"""'),
        f"got: {first_line[:60]!r}",
    )
else:
    check("constants.py exists", False, "file not found")

# --- 2. constants.py imports cleanly ---
try:
    sys.path.insert(0, str(ROOT))
    from config.constants import (
        SHIFTS,
        DEFECT_CATEGORIES,
        TARGET_ACHIEVEMENT_PCT,
        ID_PREFIX,
        DOWNTIME_REASONS,
    )

    check("constants import OK", True)
    check(
        "SHIFTS correct",
        SHIFTS == ["A", "B", "C"],
        f"got {SHIFTS}",
    )
    check(
        "DEFECT_CATEGORIES has 6",
        len(DEFECT_CATEGORIES) == 6,
        f"got {len(DEFECT_CATEGORIES)}",
    )
    check(
        "TARGET_ACHIEVEMENT_PCT = 95.0",
        TARGET_ACHIEVEMENT_PCT == 95.0,
        f"got {TARGET_ACHIEVEMENT_PCT}",
    )
    check(
        "ID_PREFIX has 18 keys",
        len(ID_PREFIX) == 18,
        f"got {len(ID_PREFIX)}",
    )
    check(
        "DOWNTIME_REASONS has 6",
        len(DOWNTIME_REASONS) == 6,
        f"got {len(DOWNTIME_REASONS)}",
    )
except Exception as e:
    check("constants import OK", False, f"{type(e).__name__}: {e}")

# --- 3. data_dictionary.md exists and has 15 tables ---
dd_path = ROOT / "docs" / "data_dictionary.md"
if dd_path.exists():
    text = dd_path.read_text(encoding="utf-8")
    first_line = text.splitlines()[0]
    table_count = sum(
        1 for line in text.splitlines() if line.startswith("### ") and line[4:5].isdigit()
    )
    check(
        "data_dictionary.md starts with # GFIS",
        first_line.startswith("# GFIS"),
        f"got: {first_line[:60]!r}",
    )
    check(
        "data_dictionary.md has 15 tables",
        table_count == 15,
        f"got {table_count}",
    )
    check(
        "no leaked @' marker",
        not first_line.strip().startswith("@'"),
    )
else:
    check("data_dictionary.md exists", False, "file not found")

# --- 4. business_requirements.md exists ---
brd_path = ROOT / "docs" / "business_requirements.md"
if brd_path.exists():
    text = brd_path.read_text(encoding="utf-8")
    first_line = text.splitlines()[0]
    check(
        "business_requirements.md starts with # GFIS",
        first_line.startswith("# GFIS"),
        f"got: {first_line[:60]!r}",
    )
    check(
        "BRD mentions Revenue recognition",
        "Revenue recognition" in text,
    )
    check(
        "no leaked @' marker",
        not first_line.strip().startswith("@'"),
    )
else:
    check("business_requirements.md exists", False, "file not found")

# --- 5. requirements.txt present ---
check(
    "requirements.txt exists",
    (ROOT / "requirements.txt").exists(),
)

# --- Summary ---
print("\n" + "=" * 45)
print(f"RESULT: {ok} passed, {fail} failed")
print("=" * 45)
if fail == 0:
    print("✅ Day 2 is CLEAN — ready for Day 3")
    sys.exit(0)
else:
    print("❌ Fix the [FAIL] items above, then re-run")
    sys.exit(1)