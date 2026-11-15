import subprocess
import difflib

files = [
    "backend/migrations/versions/0003_m43_sealing.py",
    "backend/migrations/versions/m43_sealing.sql"
]

diff_report = []

for rel_path in files:
    git_head = subprocess.check_output(["git", "show", f"HEAD:{rel_path}"], text=True).splitlines(keepends=True)
    with open(rel_path, "r", encoding="utf-8") as f:
        working = f.readlines()
        
    diff = list(difflib.unified_diff(
        git_head, working,
        fromfile=f"HEAD:{rel_path}",
        tofile=f"WORKING:{rel_path}"
    ))
    diff_report.append(f"=== Diff for {rel_path} ===")
    diff_report.extend(diff)
    diff_report.append("\n")

full_diff_text = "".join(diff_report)
print(full_diff_text)

with open("scratch/m43_diff_audit.txt", "w", encoding="utf-8") as f:
    f.write(full_diff_text)
