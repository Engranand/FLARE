import os
import json
import csv
import hashlib

BASE_DIR = r"c:\Users\anand\OneDrive\Documents\ChatGPT\FLARE"
ORIGINAL_DIR = os.path.join(BASE_DIR, "data", "raw", "challenge_resources", "original")
MANIFEST_PATH = os.path.join(BASE_DIR, "data", "raw", "challenge_resources", "manifests", "resource_manifest.json")

with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
    manifest = json.load(f)

psi117_files = [r for r in manifest["resources"] if r.get("investigation_id") == "PSI-117"]
print(f"PSI-117 resources: {len(psi117_files)}")

for r in psi117_files:
    fn = r["original_filename"]
    p = os.path.join(BASE_DIR, "data", "raw", "challenge_resources", r["path"])
    sha = r["sha256"]
    size = r["size_bytes"]
    print(f"\nFILE: {fn} ({size} bytes, sha: {sha[:12]}...)")
    if fn.endswith(".csv"):
        with open(p, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = [next(reader) for _ in range(min(4, sum(1 for _ in open(p, encoding='utf-8-sig'))))]
            print(f"  Rows 0: {rows[0]}")
            if len(rows) > 1:
                print(f"  Rows 1: {rows[1]}")
