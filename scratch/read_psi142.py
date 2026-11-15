import csv

p = "data/raw/challenge_resources/original/other/PSI-142/PSI-142_Experimental table_Data Summary Table.csv"
with open(p, "r", encoding="utf-8-sig") as f:
    for row in csv.reader(f):
        print(row)
