import zipfile
import xml.etree.ElementTree as ET
import time

def fast_profile_xlsx(path):
    t0 = time.time()
    result = {"sheets": []}
    with zipfile.ZipFile(path) as z:
        # shared strings
        shared_strings = []
        if "xl/sharedStrings.xml" in z.namelist():
            with z.open("xl/sharedStrings.xml") as f:
                # iterparse to avoid huge memory
                for event, elem in ET.iterparse(f, events=('end',)):
                    if elem.tag.endswith('t') and elem.text:
                        shared_strings.append(elem.text)
                    elem.clear()
                    if len(shared_strings) > 1000:
                        break # only need enough for headers
        
        # workbook
        with z.open("xl/workbook.xml") as f:
            wb_tree = ET.fromstring(f.read())
            ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            for s in wb_tree.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet'):
                result["sheets"].append(s.attrib.get('name'))
                
    elapsed = time.time() - t0
    result["elapsed"] = elapsed
    return result

p = "data/raw/challenge_resources/original/saffire/PSI-99/PSI-99_Raw Data_Saffire-II Telemetry Data.xlsx"
print(fast_profile_xlsx(p))
