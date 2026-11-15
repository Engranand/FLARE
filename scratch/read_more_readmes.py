import zipfile
import xml.etree.ElementTree as ET

def get_docx_text(path):
    with zipfile.ZipFile(path) as z:
        xml_content = z.read("word/document.xml")
        tree = ET.fromstring(xml_content)
        paragraphs = []
        for p in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
            texts = [node.text for node in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
            if texts:
                paragraphs.append("".join(texts))
        return "\n".join(paragraphs)

saffire_readme = "data/raw/challenge_resources/original/saffire/PSI-100/PSI-100_Science Documents_SAFFIRE-I and SAFFIRE-III Readme.docx"
text = get_docx_text(saffire_readme)
print("=== SAFFIRE-I and III Readme text preview (first 1000 chars) ===")
print(text[:1000])

bre_readme = "data/raw/challenge_resources/original/acme/PSI-20/PSI-20_Science Documents_ACME_BRE_Readme.docx"
text2 = get_docx_text(bre_readme)
print("\n=== ACME BRE Readme text preview (first 1000 chars) ===")
print(text2[:1000])
