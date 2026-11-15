import os
import json

BASE_DIR = r"c:\Users\anand\OneDrive\Documents\ChatGPT\FLARE"
MANIFEST_PATH = os.path.join(BASE_DIR, "data", "raw", "challenge_resources", "manifests", "resource_manifest.json")

with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
    manifest = json.load(f)

excel_resources = [r for r in manifest["resources"] if r["original_filename"].lower().endswith((".xlsx", ".xls"))]
print(f"Total Excel resources: {len(excel_resources)}")
for idx, r in enumerate(excel_resources, 1):
    inv = r.get("investigation_id") or "NO_INV"
    fn = r["original_filename"]
    path = os.path.join(BASE_DIR, "data", "raw", "challenge_resources", r["path"])
    size = os.path.getsize(path)
    print(f"{idx:2d}. [{inv:10s}] {size:9d} B | {fn}")
