with open("backend/app/ingestion/pipeline.py", "r", encoding="utf-8") as f:
    text = f.read()

# find CSV_HEADERS definition
idx = text.find("CSV_HEADERS")
if idx != -1:
    print(text[idx:idx+1000])
