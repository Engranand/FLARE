import zipfile
import xml.etree.ElementTree as ET

def get_docx_text(path):
    with zipfile.ZipFile(path) as z:
        xml_content = z.read("word/document.xml")
        tree = ET.fromstring(xml_content)
        # namespaces
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        paragraphs = []
        for p in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
            texts = [node.text for node in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
            if texts:
                paragraphs.append("".join(texts))
        return "\n".join(paragraphs)

bass2_readme = "data/raw/challenge_resources/original/bass_ii/PSI-25/PSI-25_Science Documents_BASS-II_ReadMe.docx"
text = get_docx_text(bass2_readme)
print("=== BASS-II Readme text preview (first 1000 chars) ===")
print(text[:1000])
print("\n=== Paragraph count:", len(text.splitlines()))
