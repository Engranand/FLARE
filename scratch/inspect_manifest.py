import json

manifest_path = "data/raw/challenge_resources/manifests/resource_manifest.json"
with open(manifest_path, "r", encoding="utf-8") as f:
    manifest = json.load(f)

print("Top level keys in manifest:")
for k, v in manifest.items():
    if isinstance(v, list):
        print(f"  {k}: list of {len(v)} items")
    elif isinstance(v, dict):
        print(f"  {k}: dict of {len(v)} keys")
    else:
        print(f"  {k}: {type(v).__name__} = {v}")
