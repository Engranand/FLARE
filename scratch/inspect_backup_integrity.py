with open("backend/app/db/backup.py", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find("def verify_database_integrity")
if idx != -1:
    print(text[idx:idx+1500])
