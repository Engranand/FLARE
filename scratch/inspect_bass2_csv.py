import hashlib
import csv

p1 = "data/raw/challenge_resources/original/bass_ii/PSI-25_Experimental table_BASS-II.csv"
p2 = "data/raw/bass_ii/original/PSI-25_Experimental table_BASS-II.csv"

def hash_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

h1 = hash_file(p1)
h2 = hash_file(p2)
print(f"P1 (challenge_resources): {h1}")
print(f"P2 (bass_ii/original)   : {h2}")
print(f"Match: {h1 == h2}")

with open(p1, "r", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    headers = next(reader)
    print(f"\nTotal headers ({len(headers)}):")
    for idx, h in enumerate(headers):
        print(f"  Col {idx:2d}: '{h}'")
    
    rows = list(reader)
    print(f"\nTotal data rows: {len(rows)}")
    print("Row 0 sample:")
    for h, v in zip(headers, rows[0]):
        print(f"  {h} = '{v}'")
