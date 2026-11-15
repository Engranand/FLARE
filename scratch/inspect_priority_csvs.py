import os
import csv
import json

BASE_DIR = r"c:\Users\anand\OneDrive\Documents\ChatGPT\FLARE\data\raw\challenge_resources"

def inspect_csv(rel_path, max_rows=5):
    full_path = os.path.join(BASE_DIR, rel_path)
    if not os.path.exists(full_path):
        return f"File not found: {full_path}"
    
    with open(full_path, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        rows = []
        for i, r in enumerate(reader):
            if i < max_rows:
                rows.append(r)
            else:
                break
    return rows

priority_files = [
    ("BASS-II", "original/bass_ii/PSI-25_Experimental table_BASS-II.csv"),
    ("Saffire-III", "original/saffire/PSI-100_Experimental table_SAFFIRE-3.csv"),
    ("Saffire-III Raw", "original/saffire/PSI-100_Raw Data_Raw telemetry file.csv"),
    ("Saffire-III Table", "original/saffire/PSI-100/PSI-100_Raw Data_Saffire_Data_Table2017.161.00.42.03-EU.csv"),
    ("ACME BRE", "original/acme/PSI-20_Experimental table_ACME BRE.csv"),
    ("ACME BRE Raw", "original/acme/PSI-20/PSI-20_Raw Data_19056A2_data.csv"),
    ("ACME CFI-G Normal", "original/acme/PSI-159_Experimental table_CFI-G_Normal Flames.csv"),
    ("ACME CFI-G Inverse", "original/acme/PSI-159_Experimental table_CFI-G_Inverse Flames.csv"),
    ("ACME CFI-G Raw", "original/acme/PSI-159/PSI-159_Raw Data_21256A1_mfcSetpoints.csv"),
    ("SAME", "original/other/PSI-102/PSI-102_Experimental table_SAME.csv"),
    ("SAME-R", "original/other/PSI-101/PSI-101_Experimental table_SAME-R.csv"),
    ("SAME-R Raw", "original/other/PSI-101/PSI-101_Raw Data_HKPData_gmt236_2.csv")
]

for label, p in priority_files:
    print("=" * 60)
    print(f"{label} => {p}")
    rows = inspect_csv(p, 4)
    if isinstance(rows, str):
        print(rows)
    else:
        for idx, r in enumerate(rows):
            print(f"  Row {idx}: {r[:12]}")
