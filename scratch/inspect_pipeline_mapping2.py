with open("backend/app/ingestion/pipeline.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

print("".join(lines[530:680]))
