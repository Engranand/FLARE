with open("backend/app/db/check.py", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if "0007_m45_n2" in line:
            print(f"Line {i}: {line.strip()}")
