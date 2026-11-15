with open("backend/app/db/check.py", "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = re.findall(r"000\d_[a-zA-Z0-9_]+", text)
print("Revisions mentioned in check.py:", set(matches))
