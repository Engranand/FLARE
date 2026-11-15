import os
import csv

psi117_dir = "data/raw/challenge_resources/original/psi_117"
csv_files = [f for f in os.listdir(psi117_dir) if f.endswith(".csv")]

for f in sorted(csv_files):
    path = os.path.join(psi117_dir, f)
    print("=" * 60)
    print(f"FILE: {f}")
    with open(path, "r", encoding="utf-8-sig") as fp:
        reader = csv.reader(fp)
        for i, row in enumerate(reader):
            if i < 8:
                print(f"  Row {i}: {row}")
            else:
                break
