with open("backend/app/ingestion/reconciliation.py", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find("CSV_HEADERS")
if idx != -1:
    print(text[idx:idx+800])
