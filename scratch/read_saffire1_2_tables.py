import csv

for path in [
    "data/raw/challenge_resources/original/saffire/PSI-98/PSI-98_Experimental table_SAFFIRE-1.csv",
    "data/raw/challenge_resources/original/saffire/PSI-99/PSI-99_Experimental table_SAFFIRE-2.csv"
]:
    print("=" * 60)
    print(path)
    with open(path, "r", encoding="utf-8-sig") as f:
        r = csv.reader(f)
        for row in r:
            print(row)
