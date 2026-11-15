import csv

p = "data/raw/challenge_resources/original/saffire/PSI-100_Raw Data_Raw telemetry file.csv"
with open(p, "r", encoding="utf-8-sig") as f:
    r = csv.reader(f)
    headers = next(r)
    print(f"Total columns: {len(headers)}")
    for i, h in enumerate(headers):
        print(f"  Col {i:2d}: {h}")
    first_row = next(r)
    print("Row 1 sample values:")
    for i, (h, val) in enumerate(zip(headers[:15], first_row[:15])):
        print(f"  {h} = {val}")
