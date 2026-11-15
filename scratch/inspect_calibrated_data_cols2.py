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
    
    rows = []
    for i, r in enumerate(ws_tree.iter(f'{ns}row')):
        if i > 2: break
        row_cells = []
        for c in r.iter(f'{ns}c'):
            v_node = c.find(f'{ns}v')
            val = v_node.text if v_node is not None else ""
            if c.attrib.get('t') == 's' and val != "":
                val = shared_strings[int(val)]
            row_cells.append(val)
        rows.append(row_cells)

for idx, (col_name, unit) in enumerate(zip(rows[0][40:], rows[1][40:]), 40):
    print(f"  Col {idx:2d}: {col_name} [{unit}]")
