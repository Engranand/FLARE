import zipfile
import xml.etree.ElementTree as ET

path = "data/raw/challenge_resources/original/saffire/PSI-100/PSI-100_Raw Data_Saffire III Sample 1 Sensors.xlsx"
with zipfile.ZipFile(path) as z:
    wb_tree = ET.fromstring(z.read("xl/workbook.xml"))
    sheet_map = {}
    for s in wb_tree.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet'):
        sheet_map[s.attrib.get('name')] = s.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
    
    # Check relationships
    rels_tree = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rel_targets = {}
    for r in rels_tree:
        rel_targets[r.attrib['Id']] = r.attrib['Target']
    
    shared_strings = []
    if "xl/sharedStrings.xml" in z.namelist():
        ss_tree = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in ss_tree.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
            texts = [t.text for t in si.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t') if t.text]
            shared_strings.append("".join(texts))
            
    for sheet_name in ['Plume Temperature', 'Sample Temperature']:
        r_id = sheet_map[sheet_name]
        target = "xl/" + rel_targets[r_id]
        ws_tree = ET.fromstring(z.read(target))
        ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
        print(f"\n=== Sheet: {sheet_name} ===")
        for i, r in enumerate(ws_tree.iter(f'{ns}row')):
            if i > 2: break
            row_cells = []
            for c in r.iter(f'{ns}c'):
                v_node = c.find(f'{ns}v')
                val = v_node.text if v_node is not None else ""
                if c.attrib.get('t') == 's' and val != "":
                    val = shared_strings[int(val)]
                row_cells.append(val)
            print(f"Row {i}: {row_cells[:20]}")
