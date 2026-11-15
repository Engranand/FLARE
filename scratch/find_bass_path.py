import json

with open("data/raw/challenge_resources/manifests/resource_manifest.json", "r", encoding="utf-8") as f:
    manifest = json.load(f)

for r in manifest["resources"]:
    if "Test.Matrices" in r["original_filename"]:
        print(r["original_filename"], "=>", r["path"])
