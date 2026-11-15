import os
import json
import csv
import re
import zipfile
import hashlib
import xml.etree.ElementTree as ET
from collections import defaultdict

BASE_DIR = r"c:\Users\anand\OneDrive\Documents\ChatGPT\FLARE"
ORIGINAL_DIR = os.path.join(BASE_DIR, "data", "raw", "challenge_resources", "original")
MANIFEST_PATH = os.path.join(BASE_DIR, "data", "raw", "challenge_resources", "manifests", "resource_manifest.json")

with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
    manifest = json.load(f)

resources = manifest["resources"]

# Load previous helper definitions
from build_inventory_and_profiles import extract_unit, classify_attribution, get_investigation_info, evaluate_compatibility

profiles = {}
inventory_rows = []

print(f"Profiling {len(resources)} resources...")

for idx, r in enumerate(resources, 1):
    res_id = r["resource_id"]
    inv_id = r.get("investigation_id")
    rel_path = r["path"]
    orig_fn = r["original_filename"]
    ext = os.path.splitext(orig_fn)[1].lower()
    full_path = os.path.join(BASE_DIR, "data", "raw", "challenge_resources", rel_path)
    
    file_exists = os.path.exists(full_path)
    size_bytes = os.path.getsize(full_path) if file_exists else 0
    recorded_sha256 = r.get("sha256", "")
    priority = r.get("priority", "P2")
    category = r.get("resource_category", "")
    
    study_name, phenomenon, gravity, materials = get_investigation_info(inv_id, orig_fn)
    comp_rating = evaluate_compatibility(inv_id, orig_fn)
    
    prof = {
        "resource_id": res_id,
        "investigation_id": inv_id,
        "study_name": study_name,
        "physical_phenomenon": phenomenon,
        "gravity_condition": gravity,
        "fuel_material": materials,
        "original_filename": orig_fn,
        "relative_path": rel_path,
        "format": ext.upper().replace(".", ""),
        "size_bytes": size_bytes,
        "sha256": recorded_sha256,
        "priority": priority,
        "compatibility_rating": comp_rating
    }
    
    row_count = None
    col_count = None
    exp_conditions = []
    meas_variables = []
    attr_types = set()
    
    if not file_exists:
        prof["status"] = "MISSING_ON_DISK"
    elif ext == ".csv":
        prof["status"] = "PROFILED"
        # Parse CSV
        try:
            with open(full_path, "r", encoding="utf-8-sig", errors="replace") as f_csv:
                reader = csv.reader(f_csv)
                raw_rows = list(reader)
            
            row_count = len(raw_rows)
            if row_count > 0:
                header_row = raw_rows[0]
                # Sometimes row 0 is metadata, row 1 is headers (like in ACME raw files or PSI-117)
                col_names = [c.strip() for c in header_row if c.strip()]
                # Check if second row looks more like headers
                if len(raw_rows) > 1 and len(col_names) < len(raw_rows[1]) / 2:
                    header_row = raw_rows[1]
                
                col_count = len(header_row)
                data_rows = raw_rows[1:]
                
                # Check duplicates
                seen_rows = set()
                dupe_count = 0
                for row_tuple in (tuple(rw) for rw in data_rows):
                    if row_tuple in seen_rows:
                        dupe_count += 1
                    else:
                        seen_rows.add(row_tuple)
                
                prof["row_count"] = row_count
                prof["column_count"] = col_count
                prof["duplicate_rows"] = dupe_count
                
                col_profiles = []
                for c_idx, h_name in enumerate(header_row):
                    clean_h = h_name.strip()
                    if not clean_h:
                        clean_h = f"Column_{c_idx+1}"
                    
                    unit = extract_unit(clean_h)
                    attr = classify_attribution(orig_fn, clean_h, inv_id)
                    attr_types.add(attr)
                    
                    if attr == "Experimental Condition / Setting" or any(k in clean_h.lower() for k in ["day", "date", "sample", "test", "material", "flow", "pressure", "o2", "xo2", "p ("]):
                        exp_conditions.append(clean_h)
                    elif attr in ["Experimental Measurement", "Derived Quantity"]:
                        meas_variables.append(clean_h)
                    
                    # Analyze values for data type and numeric range
                    vals = [rw[c_idx] for rw in data_rows if len(rw) > c_idx and rw[c_idx] != ""]
                    empty_count = len(data_rows) - len(vals)
                    
                    # Detect type
                    num_vals = []
                    for v in vals:
                        try:
                            num_vals.append(float(v))
                        except ValueError:
                            pass
                    
                    if len(num_vals) > 0 and len(num_vals) == len(vals):
                        detected_type = "float" if any("." in v or "e" in v.lower() for v in vals) else "int"
                        val_min = min(num_vals)
                        val_max = max(num_vals)
                        val_mean = sum(num_vals) / len(num_vals)
                    elif len(num_vals) > len(vals) * 0.8:
                        detected_type = "numeric_mixed"
                        val_min = min(num_vals) if num_vals else None
                        val_max = max(num_vals) if num_vals else None
                        val_mean = sum(num_vals) / len(num_vals) if num_vals else None
                    else:
                        detected_type = "string"
                        val_min = None
                        val_max = None
                        val_mean = None
                        
                    col_profiles.append({
                        "name": clean_h,
                        "index": c_idx,
                        "data_type": detected_type,
                        "unit": unit,
                        "missing_count": empty_count,
                        "attribution": attr,
                        "min": val_min,
                        "max": val_max,
                        "mean": round(val_mean, 4) if val_mean is not None else None
                    })
                prof["columns"] = col_profiles
        except Exception as e:
            prof["status"] = f"CSV_PARSE_ERROR: {str(e)}"
            
    elif ext in [".xlsx", ".xls"]:
        prof["status"] = "PROFILED"
        if ext == ".xlsx":
            try:
                with zipfile.ZipFile(full_path) as z:
                    # sheets
                    wb_tree = ET.fromstring(z.read("xl/workbook.xml"))
                    sheet_names = [s.attrib.get('name') for s in wb_tree.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet')]
                    prof["sheets"] = sheet_names
                    
                    # shared strings
                    shared_strings = []
                    if "xl/sharedStrings.xml" in z.namelist():
                        with z.open("xl/sharedStrings.xml") as f_ss:
                            for event, elem in ET.iterparse(f_ss, events=('end',)):
                                if elem.tag.endswith('t') and elem.text:
                                    shared_strings.append(elem.text)
                                elem.clear()
                                if len(shared_strings) > 200:
                                    break
                    
                    # sheet1 preview
                    if "xl/worksheets/sheet1.xml" in z.namelist():
                        with z.open("xl/worksheets/sheet1.xml") as f_ws:
                            headers = []
                            for event, elem in ET.iterparse(f_ws, events=('end',)):
                                if elem.tag.endswith('row'):
                                    r_num = elem.attrib.get('r')
                                    if r_num == '1':
                                        for c in elem:
                                            v = c.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                                            val = v.text if v is not None else ""
                                            if c.attrib.get('t') == 's' and val:
                                                val = shared_strings[int(val)] if int(val) < len(shared_strings) else val
                                            headers.append(val)
                                        break
                            prof["sheet1_headers"] = headers[:30]
                            col_count = len(headers)
                            for h in headers:
                                clean_h = str(h).strip()
                                unit = extract_unit(clean_h)
                                attr = classify_attribution(orig_fn, clean_h, inv_id)
                                attr_types.add(attr)
                                if attr == "Experimental Condition / Setting" or any(k in clean_h.lower() for k in ["sample", "fuel", "fan", "flow", "oxygen", "pressure", "igniter"]):
                                    exp_conditions.append(clean_h)
                                elif attr in ["Experimental Measurement", "Derived Quantity"]:
                                    meas_variables.append(clean_h)
            except Exception as e:
                prof["status"] = f"XLSX_PARSE_ERROR: {str(e)}"
        else:
            prof["sheets"] = ["Binary XLS Workbook"]
            col_count = None
            row_count = None
            
    elif ext == ".pdf":
        prof["status"] = "PROFILED"
        # Check if known corrupt file
        if "FLEX-1248_Summary.pdf" in orig_fn:
            prof["status"] = "CORRUPT_UPSTREAM_FILE"
            prof["pages"] = 0
            prof["notes"] = "File lacks %PDF- header; upstream NASA binary payload is corrupted."
        else:
            try:
                with open(full_path, "rb") as f_pdf:
                    content = f_pdf.read()
                page_matches = len(re.findall(rb"/Type\s*/Page\b", content))
                prof["pages"] = max(1, page_matches)
                # Title
                title_match = re.search(rb"/Title\s*\((.*?)\)", content)
                if title_match:
                    prof["pdf_title"] = title_match.group(1).decode("latin-1", errors="replace").strip()
            except Exception as e:
                prof["status"] = f"PDF_PARSE_ERROR: {str(e)}"
                
    elif ext in [".docx", ".doc"]:
        prof["status"] = "PROFILED"
        if ext == ".docx":
            try:
                with zipfile.ZipFile(full_path) as z:
                    xml_content = z.read("word/document.xml")
                    tree = ET.fromstring(xml_content)
                    paragraphs = []
                    for p in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                        texts = [node.text for node in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
                        if texts:
                            paragraphs.append("".join(texts))
                    prof["paragraph_count"] = len(paragraphs)
                    prof["word_count"] = sum(len(p.split()) for p in paragraphs)
                    prof["preview_snippet"] = "\n".join(paragraphs[:5])[:300]
            except Exception as e:
                prof["status"] = f"DOCX_PARSE_ERROR: {str(e)}"
        else:
            prof["notes"] = "Binary Legacy DOC Document"
            
    elif ext == ".zip":
        prof["status"] = "PROFILED"
        try:
            with zipfile.ZipFile(full_path) as z:
                names = z.namelist()
                prof["member_count"] = len(names)
                prof["members"] = names[:10]
        except Exception as e:
            prof["status"] = f"ZIP_PARSE_ERROR: {str(e)}"
            
    elif ext == ".txt":
        prof["status"] = "PROFILED"
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f_txt:
                lines = f_txt.readlines()
            prof["line_count"] = len(lines)
            prof["word_count"] = sum(len(l.split()) for l in lines)
        except Exception as e:
            prof["status"] = f"TXT_PARSE_ERROR: {str(e)}"
            
    profiles[res_id] = prof
    
    # Attribution summary
    if not attr_types:
        if ext == ".pdf":
            final_attr = "Scientific Publication / Report"
        elif ext in [".docx", ".doc"]:
            final_attr = "Experimental Protocol / Readme"
        elif ext == ".zip":
            final_attr = "Metadata Package (ISA-Tab / Telemetry)"
        else:
            final_attr = "Context / Reference"
    elif "Numerical Simulation" in attr_types and "Experimental Measurement" in attr_types:
        final_attr = "Mixed (Experimental & Numerical Simulation)"
    elif "Numerical Simulation" in attr_types and len(attr_types) == 1:
        final_attr = "Numerical Simulation"
    elif "Derived Quantity" in attr_types and "Experimental Measurement" not in attr_types:
        final_attr = "Derived Quantities"
    else:
        final_attr = "Experimental Measurements"

    # Clean condition and measurement strings
    cond_str = "; ".join(dict.fromkeys(exp_conditions))[:150] if exp_conditions else "None recorded in headers"
    meas_str = "; ".join(dict.fromkeys(meas_variables))[:150] if meas_variables else "None recorded in headers"

    inventory_rows.append({
        "resource_id": res_id,
        "investigation_id": inv_id or "NASA-SP",
        "relative_path": rel_path,
        "original_filename": orig_fn,
        "format": ext.upper().replace(".", ""),
        "size_bytes": size_bytes,
        "sha256": recorded_sha256,
        "priority": priority,
        "category": category,
        "gravity_condition": gravity,
        "physical_phenomenon": phenomenon,
        "fuel_material": materials,
        "row_count": row_count if row_count is not None else "",
        "column_count": col_count if col_count is not None else "",
        "experimental_conditions": cond_str,
        "measured_variables": meas_str,
        "attribution_type": final_attr,
        "compatibility_rating": comp_rating
    })

print("Profiling complete. Saving deliverables...")

# 1. Save scientific_dataset_profile.json
profile_deliverable = {
    "metadata": {
        "title": "FLARE M7 Scientific Dataset Profile & Compatibility Audit",
        "generated_utc": "2026-11-14T06:30:00Z",
        "total_resources": len(profiles),
        "total_bytes": sum(p["size_bytes"] for p in profiles.values()),
        "distinct_sha256": len(set(p["sha256"] for p in profiles.values())),
        "duplicate_groups_count": len(manifest.get("duplicate_sha256", {})),
        "upstream_corrupt_files": ["original/other/PSI-39/PSI-39_Analyzed Data_FLEX-1248_Summary.pdf"],
        "inaccessible_official_urls": manifest.get("failed_downloads", [])
    },
    "profiles": profiles
}

with open("scientific_dataset_profile.json", "w", encoding="utf-8") as f_json:
    json.dump(profile_deliverable, f_json, indent=2)
print("Saved scientific_dataset_profile.json (root)")

with open("data/raw/challenge_resources/reports/scientific_dataset_profile.json", "w", encoding="utf-8") as f_json:
    json.dump(profile_deliverable, f_json, indent=2)
print("Saved scientific_dataset_profile.json (reports)")

# 2. Save scientific_dataset_inventory.csv
fieldnames = [
    "resource_id", "investigation_id", "relative_path", "original_filename",
    "format", "size_bytes", "sha256", "priority", "category",
    "gravity_condition", "physical_phenomenon", "fuel_material",
    "row_count", "column_count", "experimental_conditions",
    "measured_variables", "attribution_type", "compatibility_rating"
]

with open("scientific_dataset_inventory.csv", "w", encoding="utf-8-sig", newline="") as f_csv:
    writer = csv.DictWriter(f_csv, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(inventory_rows)
print("Saved scientific_dataset_inventory.csv (root)")

with open("data/raw/challenge_resources/reports/scientific_dataset_inventory.csv", "w", encoding="utf-8-sig", newline="") as f_csv:
    writer = csv.DictWriter(f_csv, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(inventory_rows)
print("Saved scientific_dataset_inventory.csv (reports)")

print("Deliverable 1 and Deliverable 2 generation completed successfully!")
