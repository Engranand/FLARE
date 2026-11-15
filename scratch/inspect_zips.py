import os
import json
import zipfile

BASE_DIR = r"c:\Users\anand\OneDrive\Documents\ChatGPT\FLARE\data\raw\challenge_resources"
MANIFEST_PATH = os.path.join(BASE_DIR, "manifests", "resource_manifest.json")

with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
    manifest = json.load(f)

zip_resources = [r for r in manifest["resources"] if r["original_filename"].lower().endswith(".zip")]
print(f"Total ZIP resources: {len(zip_resources)}")

zip_summaries = {}
for r in zip_resources:
    rel_path = r["path"]
    full_path = os.path.join(BASE_DIR, rel_path)
    inv = r.get("investigation_id") or "NO_INV"
    fn = r["original_filename"]
    try:
        with zipfile.ZipFile(full_path) as z:
            names = z.namelist()
            zip_summaries[fn] = {"inv": inv, "count": len(names), "files": names[:5]}
    except Exception as e:
        zip_summaries[fn] = {"inv": inv, "error": str(e)}

for fn, s in sorted(zip_summaries.items()):
    print(f"[{s['inv']:8s}] {fn} ({s.get('count', 'ERR')} entries): {s.get('files', s.get('error'))}")
