import zipfile
import xml.etree.ElementTree as ET

path = "data/raw/challenge_resources/original/saffire/PSI-100/PSI-100_Raw Data_Saffire III Sample 1 Sensors.xlsx"
with zipfile.ZipFile(path) as z:
    shared_strings = []
    if "xl/sharedStrings.xml" in z.namelist():
        ss_tree = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in ss_tree.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
            texts = [t.text for t in si.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t') if t.text]
            shared_strings.append("".join(texts))
            
    ws_tree = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    
    first_row = ws_tree.find(f'{ns}sheetData/{ns}row')
    cells = []
    for c in first_row.iter(f'{ns}c'):
        v_node = c.find(f'{ns}v')
        val = v_node.text if v_node is not None else ""
        if c.attrib.get('t') == 's' and val != "":
            val = shared_strings[int(val)]
        cells.append((c.attrib.get('r'), val))

print(f"Total cells in first row: {len(cells)}")
for ref, val in cells[35:]:
    print(f"  {ref}: {val}")
