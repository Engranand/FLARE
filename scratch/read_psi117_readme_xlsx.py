import zipfile
import xml.etree.ElementTree as ET

path = "data/raw/challenge_resources/original/psi_117/PSI-117_Analyzed Data_ReadMe_List_of_Data.xlsx"
with zipfile.ZipFile(path) as z:
    # shared strings
    shared_strings = []
    if "xl/sharedStrings.xml" in z.namelist():
        ss_tree = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in ss_tree.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
            texts = [t.text for t in si.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t') if t.text]
            shared_strings.append("".join(texts))
            
    ws_tree = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    
    rows = []
    for r in ws_tree.iter(f'{ns}row'):
        row_cells = {}
        for c in r.iter(f'{ns}c'):
            ref = c.attrib.get('r')
            v_node = c.find(f'{ns}v')
            val = v_node.text if v_node is not None else ""
            if c.attrib.get('t') == 's' and val != "":
                val = shared_strings[int(val)]
            row_cells[ref] = val
        rows.append(row_cells)

print(f"Total rows in ReadMe_List_of_Data.xlsx: {len(rows)}")
for r in rows:
    print(r)
