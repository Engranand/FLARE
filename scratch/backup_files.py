import os
import shutil

backup_dir = "scratch/backup_m43"
os.makedirs(backup_dir, exist_ok=True)

f1 = "backend/migrations/versions/0003_m43_sealing.py"
f2 = "backend/migrations/versions/m43_sealing.sql"

shutil.copy2(f1, os.path.join(backup_dir, "0003_m43_sealing.py.bak"))
shutil.copy2(f2, os.path.join(backup_dir, "m43_sealing.sql.bak"))

print("Safety backups created in scratch/backup_m43/")
print("Files backed up:")
print(" -", os.path.join(backup_dir, "0003_m43_sealing.py.bak"))
print(" -", os.path.join(backup_dir, "m43_sealing.sql.bak"))
