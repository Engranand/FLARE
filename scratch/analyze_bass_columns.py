import csv
import json
from collections import defaultdict

csv_path = "data/raw/challenge_resources/original/bass_ii/PSI-25_Experimental table_BASS-II.csv"

with open(csv_path, "r", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    headers = next(reader)
    rows = list(reader)

print(f"Total rows: {len(rows)}")

col_stats = []
for idx, h in enumerate(headers):
    vals = [r[idx] for r in rows]
    empty_cnt = sum(1 for v in vals if v.strip() == "")
    unique_vals = sorted(list(set(vals)))
    numeric_vals = []
    non_numeric = []
    for v in vals:
        try:
            numeric_vals.append(float(v))
        except ValueError:
            non_numeric.append(v)
            
    col_stats.append({
        "index": idx,
        "header": h,
        "empty_count": empty_cnt,
        "unique_count": len(unique_vals),
        "sample_unique": unique_vals[:8],
        "is_all_numeric": len(numeric_vals) == len(rows),
        "non_numeric_samples": list(set(non_numeric))[:5],
        "min": min(numeric_vals) if numeric_vals else None,
        "max": max(numeric_vals) if numeric_vals else None,
    })

for s in col_stats:
    print("=" * 60)
    print(f"Col {s['index']:2d}: '{s['header']}'")
    print(f"  Empty count: {s['empty_count']} / {len(rows)}")
    print(f"  Unique count: {s['unique_count']}")
    print(f"  Sample unique: {s['sample_unique']}")
    if not s['is_all_numeric']:
        print(f"  Non-numeric samples: {s['non_numeric_samples']}")
    else:
        print(f"  Numeric range: [{s['min']}, {s['max']}]")
