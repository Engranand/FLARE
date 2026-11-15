import json

with open("data/raw/challenge_resources/manifests/resource_manifest.json", "r", encoding="utf-8") as f:
    manifest = json.load(f)

for r in manifest["resources"]:
    if "8390bbf4" in r["sha256"]:
        print(r["original_filename"], r["path"])
