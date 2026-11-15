with open("backend/app/ingestion/pipeline.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Total lines in pipeline.py: {len(lines)}")
inserts = []
for i, line in enumerate(lines):
    if "INSERT INTO" in line:
        inserts.append((i+1, line.strip()))

print(f"Total INSERT statements in pipeline.py: {len(inserts)}")
for line_no, stmt in inserts:
    print(f"  Line {line_no:4d}: {stmt}")
