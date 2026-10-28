"""GFIS Day 1 verification. Run: python verify_day1.py"""
import sys
import platform

checks = []

# 1. Python version
v = sys.version_info
checks.append(("Python >= 3.11", f"{v.major}.{v.minor}.{v.micro}", v >= (3, 11)))

# 2. Core imports
try:
    import pandas, numpy, duckdb, streamlit, plotly, matplotlib, pytest
    checks.append(("Core packages import", "OK", True))
except ImportError as e:
    checks.append(("Core packages import", str(e), False))

# 3. Venv active
import os
in_venv = sys.prefix != sys.base_prefix
checks.append(("Virtual env active", sys.prefix, in_venv))

# 4. OS
checks.append(("OS", platform.platform(), True))

print("\n=== GFIS Day 1 Verification ===\n")
all_ok = True
for name, detail, ok in checks:
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {name}: {detail}")
    all_ok = all_ok and ok

print("\n" + ("=" * 40))
print("RESULT:", "ALL PASS — Day 1 complete!" if all_ok else "Some checks failed — see above")
print("=" * 40)
sys.exit(0 if all_ok else 1)
