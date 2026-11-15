with open("backend/app/db/backup.py", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if "EXPECTED_ALEMBIC_HEAD" in line:
            print(f"Line {i}: {line.strip()}")
