import json

with open("scientific_dataset_profile.json", "r", encoding="utf-8") as f:
    prof = json.load(f)

profiles = prof["profiles"]

check_files = [
    "PSI-25_Experimental table_BASS-II.csv",
    "PSI-100_Raw Data_Raw telemetry file.csv",
    "PSI-20_Experimental table_ACME BRE.csv",
    "PSI-159_Experimental table_CFI-G_Normal Flames.csv",
    "PSI-102_Experimental table_SAME.csv",
    "PSI-117_Analyzed Data_MST_2024_Kavg.csv"
]

for fn in check_files:
    for pid, p in profiles.items():
        if p["original_filename"] == fn:
            print(f"{fn:55s} => {p['sha256']}")
