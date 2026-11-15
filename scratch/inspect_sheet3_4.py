import zipfile
import xml.etree.ElementTree as ET

path = "data/raw/challenge_resources/original/saffire/PSI-100/PSI-100_Raw Data_Saffire III Sample 1 Sensors.xlsx"
with zipfile.ZipFile(path) as z:
    for s_id in ["sheet3", "sheet4"]:
        xml_content = z.read(f"xl/worksheets/{s_id}.xml")
        root = ET.fromstring(xml_content)
        ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
        print(f"=== {s_id} ===")
        # print first 2 rows
        for i, row in enumerate(root.iter(f'{ns}row')):
            if i > 2: break
            vals = [c.find(f'{ns}v').text if c.find(f'{ns}v') is not None else "" for c in row.iter(f'{ns}c')]
            print(f"Row {i}: {vals[:10]}")
