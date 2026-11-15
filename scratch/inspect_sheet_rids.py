import zipfile
import xml.etree.ElementTree as ET

path = "data/raw/challenge_resources/original/saffire/PSI-100/PSI-100_Raw Data_Saffire III Sample 1 Sensors.xlsx"
with zipfile.ZipFile(path) as z:
    wb_tree = ET.fromstring(z.read("xl/workbook.xml"))
    for s in wb_tree.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet'):
        print(s.attrib.get('name'), "=>", s.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'))
