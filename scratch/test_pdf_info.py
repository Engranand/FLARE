import re
import os

def quick_pdf_info(path):
    with open(path, "rb") as f:
        data = f.read(50000) # read first 50KB
        f.seek(max(0, os.path.getsize(path) - 50000))
        tail = f.read(50000)
    
    # page count: count /Type /Page (with word boundary)
    with open(path, "rb") as f:
        content = f.read()
    
    # count /Type\s*/Page\b but not /Pages
    pages = len(re.findall(rb"/Type\s*/Page\b", content))
    
    # title
    title_match = re.search(rb"/Title\s*\((.*?)\)", content) or re.search(rb"/Title\s*<([0-9a-fA-F]+)>", content)
    title = ""
    if title_match:
        try:
            raw = title_match.group(1)
            if b"<" in title_match.group(0):
                title = bytes.fromhex(raw.decode()).decode("utf-16", errors="replace")
            else:
                title = raw.decode("latin1", errors="replace")
        except:
            title = str(title_match.group(1))
            
    return {"pages": pages, "title": title}

sample_pdf = "data/raw/challenge_resources/original/other/NASA/advanced-combustion-via-microgravity-experiments-acme.pdf"
print(quick_pdf_info(sample_pdf))
