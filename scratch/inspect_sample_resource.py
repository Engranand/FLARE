import json

manifest_path = "data/raw/challenge_resources/manifests/resource_manifest.json"
with open(manifest_path, "r", encoding="utf-8") as f:
    manifest = json.load(f)

sample = manifest["resources"][0]
print("Keys in resource record:", list(sample.keys()))
for k, v in sample.items():
    if isinstance(v, str) and len(v) > 100:
        print(f"  {k}: {v[:100]}...")
    elif isinstance(v, (list, dict)):
        print(f"  {k}: {type(v).__name__} (len {len(v)})")
    else:
        print(f"  {k}: {v}")
