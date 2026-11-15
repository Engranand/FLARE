import csv

p = "data/raw/challenge_resources/original/saffire/PSI-100/PSI-100_Experimental table_SAFFIRE-3.csv"
with open(p, "r", encoding="utf-8-sig") as f:
    r = csv.reader(f)
    for row in r:
        print(row)
