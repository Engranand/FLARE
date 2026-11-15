import os
import json
import hashlib
from collections import defaultdict

BASE_DIR = r"c:\Users\anand\OneDrive\Documents\ChatGPT\FLARE"
ORIGINAL_DIR = os.path.join(BASE_DIR, "data", "raw", "challenge_resources", "original")
MANIFEST_PATH = os.path.join(BASE_DIR, "data", "raw", "challenge_resources", "manifests", "resource_manifest.json")

with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
    manifest = json.load(f)

resources = manifest["resources"]
print(f"Total cataloged resources: {len(resources)}")

format_counts = defaultdict(int)
investigation_counts = defaultdict(int)
hash_to_files = defaultdict(list)
missing_files = []
hash_mismatches = []
corrupted_files = []

for r in resources:
    rel_path = r["path"]
    full_path = os.path.join(BASE_DIR, "data", "raw", "challenge_resources", rel_path)
    inv_id = r.get("investigation_id", "UNKNOWN")
    investigation_counts[inv_id] += 1
    
    ext = os.path.splitext(r["original_filename"])[1].lower()
    format_counts[ext] += 1
    
    if not os.path.exists(full_path):
        missing_files.append((rel_path, r["sha256"]))
        continue
    
    # Check SHA-256
    h = hashlib.sha256()
    with open(full_path, "rb") as f_in:
        while chunk := f_in.read(1024 * 1024):
            h.update(chunk)
    actual_hash = h.hexdigest()
    
    if actual_hash != r["sha256"]:
        hash_mismatches.append((rel_path, r["sha256"], actual_hash))
    
    hash_to_files[actual_hash].append(rel_path)
    
    if r.get("format_status") != "VERIFIED":
        corrupted_files.append((rel_path, r.get("format_status"), r.get("format")))

print(f"\nMissing files on disk: {len(missing_files)}")
print(f"SHA-256 mismatches: {len(hash_mismatches)}")
print(f"Files with non-VERIFIED format_status: {len(corrupted_files)}")
for c in corrupted_files:
    print(f"  {c}")

print("\nFormat breakdown (by extension):")
for ext, count in sorted(format_counts.items(), key=lambda x: -x[1]):
    print(f"  {ext:10s}: {count}")

print(f"\nTotal distinct SHA-256: {len(hash_to_files)}")
duplicate_groups = {k: v for k, v in hash_to_files.items() if len(v) > 1}
print(f"Duplicate content groups: {len(duplicate_groups)} groups ({sum(len(v) for v in duplicate_groups.values())} files total)")

print(f"\nInvestigations ({len(investigation_counts)} total):")
for inv, cnt in sorted(investigation_counts.items(), key=lambda x: -x[1]):
    print(f"  {inv:20s}: {cnt}")
