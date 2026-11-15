import os
import json
import csv
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict

BASE_DIR = r"c:\Users\anand\OneDrive\Documents\ChatGPT\FLARE"
ORIGINAL_DIR = os.path.join(BASE_DIR, "data", "raw", "challenge_resources", "original")
MANIFEST_PATH = os.path.join(BASE_DIR, "data", "raw", "challenge_resources", "manifests", "resource_manifest.json")

with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
    manifest = json.load(f)

resources = manifest["resources"]

UNIT_PATTERNS = [
    r'\(([^)]+)\)',
    r'\[([^\]]+)\]',
    r'in\s+([a-zA-Z0-9\/\^]+)$'
]

def extract_unit(header):
    if not isinstance(header, str):
        return ""
    for pat in UNIT_PATTERNS:
        m = re.search(pat, header)
        if m:
            candidate = m.group(1).strip()
            if any(u in candidate.lower() for u in ['mm', 'cm', 'm', 's', 'sec', 'k', 'c', 'w', 'atm', 'bar', 'psia', 'mg', 'g', 'kg', 'rpm', '%', 'volts', 'amps', 'mv', 'mw']):
                return candidate
    return ""

def classify_attribution(filename, col_name, inv_id):
    fn_lower = filename.lower()
    col_lower = str(col_name).lower()
    
    if "model" in col_lower or "sim" in col_lower or "tad" in col_lower or "theory" in col_lower:
        return "Numerical Simulation"
    if "errorbar" in col_lower or "uncertainty" in col_lower:
        return "Uncertainty / Error Bound"
    
    if inv_id == "PSI-117":
        if "proci_2019_oscillatory" in fn_lower or "proci_2019_stable" in fn_lower:
            return "Numerical Simulation"
        if "alkane_extinction" in fn_lower:
            if "sim" in col_lower:
                return "Numerical Simulation"
            elif "expt" in col_lower:
                return "Experimental Measurement"
        if "c12_extinction_diameter_vs_pressure" in fn_lower:
            if "model" in col_lower:
                return "Numerical Simulation"
            elif "expt" in col_lower:
                return "Experimental Measurement"
        if "burning_history" in fn_lower or "three_stage" in fn_lower or "radiance_flame_diameter" in fn_lower:
            if "model" in col_lower or "sim" in col_lower:
                return "Numerical Simulation"
            if any(k in col_lower for k in ["k(", "k_", "d/do", "(d/do)2"]):
                return "Derived Quantity"
            return "Experimental Measurement"
        if "kavg" in fn_lower:
            if "model" in col_lower:
                return "Numerical Simulation"
            return "Derived Quantity"
        if "dext" in fn_lower:
            if "model" in col_lower:
                return "Numerical Simulation"
            return "Experimental Measurement"

    if inv_id in ["PSI-60", "PSI-62", "PSI-115", "PSI-142"]:
        if "model" in fn_lower or "simulation" in fn_lower:
            return "Numerical Simulation"

    if any(k in col_lower for k in ["p@", "tc", "anemometer", "radiometer", "temp", "volt", "curr", "pres", "flux", "rpm", "gain", "time", "elapsed", "epoch"]):
        return "Experimental Measurement"
    if any(k in col_lower for k in ["kavg", "burnrate", "rate", "d/do", "spread", "velocity_calc"]):
        return "Derived Quantity"
    if any(k in col_lower for k in ["setpoint", "gain", "mode", "counter", "index", "sample", "flow restrictor", "fuel", "material", "oxygen", "pressure", "day"]):
        return "Experimental Condition / Setting"
        
    return "Experimental Measurement"

INV_METADATA = {
    "PSI-10": ("ACME Flame Design", "Gaseous diffusion flames (normal & inverse)", "Microgravity (ISS CIR)", "C2H4, CH4, Diluents"),
    "PSI-20": ("ACME BRE", "Porous burner solid emulator flame extinction", "Microgravity (ISS CIR)", "Ethylene, Methane, N2/O2"),
    "PSI-21": ("ACME CLD Flame", "Cool flame and lifted flame dynamics", "Microgravity (ISS CIR)", "Gaseous fuels"),
    "PSI-22": ("ACME E-FIELD Flames", "Electric field effects on soot & flame stability", "Microgravity (ISS CIR)", "Ethylene, Methane, Air/O2"),
    "PSI-23": ("ACME s-Flame", "Spherical & sooting flame extinction", "Microgravity (ISS CIR)", "Gaseous fuels"),
    "PSI-25": ("BASS-II", "Solid surface flame spread, extinction, airflow", "Microgravity (ISS MSG)", "PMMA, Cotton-Fiberglass (SIBAL), Nomex"),
    "PSI-26": ("BASS-I", "Solid material combustion & suppression", "Microgravity (ISS MSG)", "PMMA, Cotton fabric, Candle"),
    "PSI-39": ("CFI", "Droplet cool flame appearance and extinction", "Microgravity (ISS CIR/MDCA)", "n-Heptane, n-Octane, Alkane mixtures"),
    "PSI-47": ("DAFT", "Smoke detector response & particulate loading", "Microgravity (ISS)", "Overheated materials, Smoke aerosols"),
    "PSI-60": ("ACME Computational Modeling", "Numerical simulation of microgravity diffusion flames", "Microgravity (Simulated)", "Gaseous fuels"),
    "PSI-62": ("Concurrent Flame Spread Modeling", "Numerical simulation of solid flame spread", "Microgravity (Simulated)", "Thin solids, Fabric"),
    "PSI-68": ("FLEX-2", "Droplet combustion, binary fuels, cool flames", "Microgravity (ISS CIR/MDCA)", "Alkanes, Alcohols, Heptane"),
    "PSI-69": ("FLEX", "Flame Extinguishment Experiment, droplet burning", "Microgravity (ISS CIR/MDCA)", "n-Heptane, Methanol, Ethanol"),
    "PSI-98": ("Saffire-I", "Spacecraft-scale solid flame spread (large sample)", "Microgravity (Cygnus Cargo Vehicle)", "Cotton-Fiberglass (SIBAL cloth, 0.4m x 1.0m)"),
    "PSI-99": ("Saffire-II", "Spacecraft material flammability screening", "Microgravity (Cygnus Cargo Vehicle)", "Silicone, SIBAL, PMMA, Nomex"),
    "PSI-100": ("Saffire-III", "Large-scale flame growth & airflow extinction", "Microgravity (Cygnus Cargo Vehicle)", "Cotton-Fiberglass (SIBAL cloth, 0.4m x 1.0m)"),
    "PSI-101": ("SAME-R", "Smoke aerosol measurement & aging in space", "Microgravity (ISS)", "Pyrolyzed Kapton, Teflon, Cotton wick, Silicone"),
    "PSI-102": ("SAME", "Smoke aerosol particle size distributions", "Microgravity (ISS)", "Teflon, Silicone, Lamp wick"),
    "PSI-106": ("SLICE", "Structure & liftoff in combustion experiments", "Microgravity (ISS MSG)", "Gaseous diffusion flames"),
    "PSI-107": ("SPICE", "Smoke point in co-flow diffusion flames", "Microgravity (ISS MSG)", "Gas/sooting fuels"),
    "PSI-115": ("ACME Tomography Modeling", "Soot radiation and extinction tomography", "Microgravity (Simulated/Flight)", "Ethylene diffusion flames"),
    "PSI-117": ("Droplet Cool Flames (Farouk et al.)", "Droplet warm/cool flame transition & extinction", "Microgravity (ISS Flight & Multi-physics CFD)", "n-Heptane, n-Decane, n-Dodecane"),
    "PSI-142": ("Soot Quantitative Modeling", "Laser diagnostics & soot formation kinetics", "Microgravity & 1-g Ground", "Ethylene, Nitrogen, Oxygen"),
    "PSI-159": ("ACME CFI-G", "Cool flames in gaseous diffusion (normal & inverse)", "Microgravity (ISS CIR)", "Ethane, Ethylene, Propane, O2/N2/CO2/He"),
    "NASA": ("NASA Technical Documents & Guides", "Spacecraft fire safety & combustion overviews", "Microgravity / Spaceflight", "Spacecraft materials, Life support systems"),
    "NTRS-20210011521": ("Saffire ICES 2021 Paper", "Spacecraft fire safety experiment technical review", "Microgravity (Cygnus)", "SIBAL, PMMA, Nomex, Silicone"),
    "NTRS-20240007488": ("Saffire ICES 2024 Presentation", "Saffire-IV/V/VI elevated oxygen & low pressure", "Microgravity (Cygnus)", "Spacecraft materials, Exploration atmospheres"),
    "NTRS-20010059376": ("Microgravity Combustion Reference", "Droplet and solid combustion historical reference", "Microgravity", "Alkanes, Polymers")
}

def get_investigation_info(inv_id, filename):
    if inv_id and inv_id in INV_METADATA:
        return INV_METADATA[inv_id]
    fn_low = filename.lower()
    if "saffire" in fn_low:
        return INV_METADATA["NASA"]
    if "acme" in fn_low:
        return INV_METADATA["PSI-10"]
    return ("Microgravity Combustion Study", "Combustion phenomena in microgravity", "Microgravity", "Aerospace materials / fuels")

# Compatibility rating logic for investigation vs 7 capabilities
def evaluate_compatibility(inv_id, filename):
    inv = inv_id or ""
    fn = filename.lower()
    
    # Priority investigations mapping
    if inv in ["PSI-25", "PSI-26"]:
        return "DIRECTLY COMPARABLE (Flame Spread, Extinction, Oxygen Flammability Limits)"
    elif inv in ["PSI-98", "PSI-100"]:
        return "COMPLEMENTARY (Spacecraft-Scale Growth, Macro Boundary Layer Scaling Required)"
    elif inv == "PSI-99":
        return "COMPLEMENTARY (Material Screening, Multi-material Flammability Limits)"
    elif inv == "PSI-20":
        return "COMPLEMENTARY (Condensed-Phase Burning Rate Emulator, Surface Heat Flux Extinction)"
    elif inv == "PSI-159":
        return "COMPLEMENTARY (Cool Flame Kinetics, Low-Temperature Gaseous Extinction Boundaries)"
    elif inv in ["PSI-101", "PSI-102", "PSI-47"]:
        return "DIRECTLY COMPARABLE (Smoke Particle Agglomeration, Particulate Detection Analysis)"
    elif inv == "PSI-117":
        return "COMPLEMENTARY (Droplet Cool Flame Extinction & Hybrid CFD Kinetics Benchmark)"
    elif inv in ["PSI-39", "PSI-68", "PSI-69"]:
        return "COMPLEMENTARY (Spherical Droplet Combustion & Suppression Benchmark)"
    elif inv in ["PSI-10", "PSI-21", "PSI-22", "PSI-23", "PSI-106", "PSI-107"]:
        return "QUALITATIVE ONLY (Burner-Specific Flame Liftoff, Soot Diagnostics & Field Effects)"
    elif inv in ["PSI-60", "PSI-62", "PSI-115", "PSI-142"]:
        return "QUALITATIVE ONLY (Numerical Kinetic & Radiation Models, Synthetic Benchmark)"
    else:
        return "QUALITATIVE ONLY (Scientific & Technical Background Documentation)"

print("Starting deep profiling of all 261 files...")
