import zipfile
import xml.etree.ElementTree as ET

path = "data/raw/challenge_resources/original/saffire/PSI-99/PSI-99_Raw Data_Saffire-II Telemetry Data.xlsx"
with zipfile.ZipFile(path) as z:
    shared_strings = []
    with z.open("xl/sharedStrings.xml") as f:
        for event, elem in ET.iterparse(f, events=('end',)):
            if elem.tag.endswith('t') and elem.text:
                shared_strings.append(elem.text)
            elem.clear()
            if len(shared_strings) > 100:
                break
                
    # get sheet1
    with z.open("xl/worksheets/sheet1.xml") as f:
        for event, elem in ET.iterparse(f, events=('end',)):
            if elem.tag.endswith('row'):
                r_num = elem.attrib.get('r')
                if r_num == '1':
                    cells = []
                    for c in elem:
                        v = c.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                        val = v.text if v is not None else ""
                        if c.attrib.get('t') == 's' and val:
                            val = shared_strings[int(val)] if int(val) < len(shared_strings) else val
                        cells.append((c.attrib.get('r'), val))
                    print(f"Row 1 cells ({len(cells)} total):")
                    for ref, val in cells[:25]:
                        print(f"  {ref}: {val}")
                    break
