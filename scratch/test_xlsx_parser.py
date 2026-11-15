import zipfile
import xml.etree.ElementTree as ET

def inspect_xlsx(path):
    with zipfile.ZipFile(path) as z:
        # Get sheet names
        wb_xml = z.read("xl/workbook.xml")
        wb_tree = ET.fromstring(wb_xml)
        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        
        sheet_info = []
        for s in wb_tree.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet'):
            sheet_name = s.attrib.get('name')
            r_id = s.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
            sheet_info.append((sheet_name, r_id))
            
        # Read shared strings if available
        shared_strings = []
        if "xl/sharedStrings.xml" in z.namelist():
            ss_xml = z.read("xl/sharedStrings.xml")
            ss_tree = ET.fromstring(ss_xml)
            for si in ss_tree.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
                texts = [t.text for t in si.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t') if t.text]
                shared_strings.append("".join(texts))
        
        sheets = {}
        # Parse worksheet dimensions and headers
        sheet_num = 1
        for s_name, r_id in sheet_info:
            target_xml = f"xl/worksheets/sheet{sheet_num}.xml"
            if target_xml in z.namelist():
                ws_xml = z.read(target_xml)
                ws_tree = ET.fromstring(ws_xml)
                dim_node = ws_tree.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}dimension')
                dim_ref = dim_node.attrib.get('ref') if dim_node is not None else "Unknown"
                
                # Extract first row values (headers)
                first_row = ws_tree.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheetData/{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row')
                headers = []
                if first_row is not None:
                    for c in first_row.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                        v_node = c.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                        cell_type = c.attrib.get('t')
                        if v_node is not None and v_node.text is not None:
                            val = v_node.text
                            if cell_type == 's' and int(val) < len(shared_strings):
                                val = shared_strings[int(val)]
                            headers.append(val)
                sheets[s_name] = {"dimension": dim_ref, "headers": headers}
            sheet_num += 1
        return sheets

xlsx_path = "data/raw/challenge_resources/original/psi_117/PSI-117_Analyzed Data_ReadMe_List_of_Data.xlsx"
info = inspect_xlsx(xlsx_path)
print("=== PSI-117 ReadMe_List_of_Data.xlsx ===")
for s_name, data in info.items():
    print(f"Sheet: {s_name} | Dim: {data['dimension']} | Headers: {data['headers'][:5]}")

bass_xlsx = "data/raw/challenge_resources/original/bass_ii/PSI-25/PSI-25_Science Documents_BASS-II_Test.Matrices.xlsx"
info2 = inspect_xlsx(bass_xlsx)
print("\n=== BASS-II Test.Matrices.xlsx ===")
for s_name, data in info2.items():
    print(f"Sheet: {s_name} | Dim: {data['dimension']} | Headers: {data['headers'][:5]}")
