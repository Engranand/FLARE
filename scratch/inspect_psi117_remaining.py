import os
import csv

psi117_dir = "data/raw/challenge_resources/original/psi_117"
files = [
    "PSI-117_Analyzed Data_PROCI_2019_Oscillatory_Cool_Flame.csv",
    "PSI-117_Analyzed Data_PROCI_2019_Stable_Cool.csv",
    "PSI-117_Analyzed Data_PROCI_2023_Alkane_Extinction_Diameter_1atm.csv"
]

for f in files:
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
