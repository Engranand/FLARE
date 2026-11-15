import csv

with open("scientific_dataset_inventory.csv", "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if "BASS-II.csv" in row["original_filename"]:
            print("inventory.csv:")
            print("  Filename:", row["original_filename"])
            print("  SHA256  :", row["sha256"])
            print("  Size    :", row["size_bytes"])
            print("  Rows    :", row["row_count"])
            print("  Cols    :", row["column_count"])
