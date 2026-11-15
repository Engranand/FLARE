import os
import json
import csv
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict

BASE_DIR = r"c:\Users\anand\OneDrive\Documents\ChatGPT\FLARE"
RESOURCES_DIR = os.path.join(BASE_DIR, "data", "raw", "challenge_resources")
MANIFEST_PATH = os.path.join(RESOURCES_DIR, "manifests", "resource_manifest.json")

with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
    manifest = json.load(f)

print(f"Loaded manifest with {len(manifest['resources'])} resources.")
