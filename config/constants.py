python -c @"
import textwrap
content = textwrap.dedent('''
\"\"\"GFIS shared constants. Import these instead of hardcoding.\"\"\"
from pathlib import Path

# --- Paths ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
SAMPLE_DATA_DIR = DATA_DIR / 'sample'
DUCKDB_PATH = DATA_DIR / 'gfis.duckdb'

# --- Entity ID prefixes ---
ID_PREFIX = {
    'order': 'ORD',
    'style': 'STY',
    'line': 'LN',
    'buyer': 'BUY',
    'supplier': 'SUP',
    'material': 'MAT',
    'machine': 'MAC',
    'worker': 'WRK',
    'revenue': 'REV',
    'expense': 'EXP',
    'inspection': 'QC',
    'downtime': 'DT',
    'inventory_txn': 'INV',
    'purchase_order': 'PO',
    'cash_flow': 'CF',
    'maintenance': 'MT',
    'shipment': 'SHP',
    'production_plan': 'PLN',
}

# --- Enums ---
SHIFTS = ['A', 'B', 'C']
DEPARTMENTS = ['Cutting', 'Sewing', 'Finishing', 'Packing']
ORDER_STATUSES = ['Open', 'InProduction', 'Shipped', 'Closed', 'Cancelled']
EXPENSE_CATEGORIES = [
    'Material', 'Labor', 'Electricity', 'Transport',
    'Overtime', 'Overhead', 'Maintenance', 'Other',
]
DEFECT_CATEGORIES = ['Stitch', 'Measurement', 'Fabric', 'Stain', 'Trimming', 'Other']
DEFECT_SEVERITIES = ['Minor', 'Major', 'Critical']
DOWNTIME_REASONS = [
    'Breakdown', 'Changeover', 'MaterialShortage',
    'NoOperator', 'Power', 'Scheduled',
]
INVENTORY_TXN_TYPES = ['Opening', 'Receipt', 'Issue', 'Adjustment']
MATERIAL_TYPES = ['Fabric', 'Trims', 'Accessories']
SHIPMENT_MODES = ['Sea', 'Air']
INSPECTION_STAGES = ['InLine', 'EndLine', 'Final']

# --- KPI target defaults (synthetic demo) ---
TARGET_ACHIEVEMENT_PCT = 95.0
TARGET_LINE_EFFICIENCY_PCT = 65.0
TARGET_DEFECT_RATE_PCT = 3.0
TARGET_REWORK_RATE_PCT = 2.0
TARGET_FIRST_PASS_YIELD_PCT = 95.0
TARGET_ON_TIME_DELIVERY_PCT = 90.0
TARGET_DOWNTIME_RATE_PCT = 5.0
TARGET_INVENTORY_TURNOVER = 6.0
OVERTIME_PREMIUM = 1.5
''')
with open('config/constants.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('WROTE config/constants.py OK')
"@