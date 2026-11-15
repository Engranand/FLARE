import json

with open("data/raw/challenge_resources/manifests/resource_manifest.json", "r", encoding="utf-8") as f:
    manifest = json.load(f)

for r in manifest["resources"]:
    if "BASS-II.csv" in r["original_filename"]:
        print(r["original_filename"])
        print("  Path in manifest:", r["path"])
        print("  SHA in manifest :", r["sha256"])
        print("  Size in manifest:", r["size_bytes"])
