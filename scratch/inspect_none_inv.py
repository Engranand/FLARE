import json

with open("data/raw/challenge_resources/manifests/resource_manifest.json", "r", encoding="utf-8") as f:
    manifest = json.load(f)

none_inv = [r for r in manifest["resources"] if not r.get("investigation_id")]
print(f"Resources with no investigation_id: {len(none_inv)}")
for r in none_inv:
    print(f"  {r['original_filename']} | {r['path']} | {r['size_bytes']} bytes")
