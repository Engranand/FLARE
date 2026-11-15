"""Read-only scientific presentation adapters; M9 remains the calculation authority."""
from collections import Counter
from decimal import Decimal, InvalidOperation
from typing import Any

from app.analysis.engine import AUTHENTIC_SHA256, load_authenticated_records
from app.analysis.p1_env_stats import compute_sample_median, compute_quantile_r7
from app.analysis.p2_oxygen import classify_oxygen_record
from app.analysis.p3_airflow import classify_airflow_record
from app.analysis.p4_morphology import classify_morphology_record

SOURCE = 'PSI-25_Experimental table_BASS-II.csv'
O2 = 'Calibrated  initial O2 % by vol '


def number(value):
    try:
        n = Decimal(str(value).strip())
        return n if n.is_finite() else None
    except (InvalidOperation, ValueError):
        return None


def distribution(key, title, unit, entries, total, notes):
    """Presentation-only equal-width binning; summary statistics reuse M9."""
    values = sorted(v for v, _ in entries)
    bins = []
    if values:
        low, high = values[0], values[-1]
        width = (high - low) / Decimal(10) if high != low else Decimal(1)
        for i in range(10 if high != low else 1):
            left, right = low + width * i, low + width * (i + 1)
            members = [(v, row) for v, row in entries if left <= v and (v < right or i == 9 or high == low)]
            bins.append({'label': f'{left:.4g} – {right:.4g}', 'low': float(left), 'high': float(right), 'count': len(members), 'rows': [row for _, row in members]})
    return {'key': key, 'title': title, 'unit': unit, 'sample_size': len(values), 'excluded': total-len(values),
            'median': str(compute_sample_median(values)) if values else None,
            'q1': str(compute_quantile_r7(values, .25)) if values else None,
            'q3': str(compute_quantile_r7(values, .75)) if values else None,
            'bins': bins, 'notes': notes, 'source': SOURCE, 'sha256': AUTHENTIC_SHA256}


def science_data(records=None):
    records = load_authenticated_records() if records is None else records
    oxygen = [classify_oxygen_record(r) for r in records]
    airflow = [classify_airflow_record(r) for r in records]
    counts = Counter(str(r['Sample #']) for r in records)
    seen = {}
    morphology = [classify_morphology_record(r, seen, {k for k, v in counts.items() if v > 1}) for r in records]
    charts = []
    for key, title, field, unit, scale in [
        ('initial_o2', 'Initial oxygen distribution', O2, 'mol/mol', Decimal('.01')),
        ('co2', 'Initial carbon dioxide', 'Initial CO2 % by vol', 'mol/mol', Decimal('.01')),
        ('co', 'Initial carbon monoxide', 'Initial CO ppm', 'ppm', Decimal(1)),
    ]:
        # Resolve exact original field spelling, never infer a measurement value.
        if key != 'initial_o2':
            candidates = [h for h in records[0] if ('initial' in h.lower() and (('co2' in h.lower()) if key == 'co2' else ('co ' in h.lower() and 'co2' not in h.lower())))] if records else []
            field = candidates[0] if len(candidates) == 1 else field
        entries = [(number(r.get(field)) * scale, r['csv_record_number']) for r in records if number(r.get(field)) is not None]
        charts.append(distribution(key, title, unit, entries, len(records), ['M9 P1 source-unit conversion. Missing, saturated and ambiguous strings are excluded without imputation. Negative CO values remain signed.', f'Source column: {field}']))
    charts.append(distribution('final_o2', 'Final oxygen • eligible paired records', 'mol/mol', [(r.final_o2_vol_pct / 100, r.csv_record_number) for r in oxygen if r.is_eligible_signed_cdf], len(records), ['M9 P2: gross anomalies and missing finals excluded.']))
    charts.append(distribution('depletion', 'Signed oxygen depletion', 'mol/mol', [(r.delta_o2_mol_fraction, r.csv_record_number) for r in oxygen if r.is_eligible_signed_cdf], len(records), ['M9 P2 signed population. Negative drift retained; it is not evidence of oxygen production. Gross anomalies remain visible in quality partitions.']))
    eligible = [r for r in airflow if r.is_eligible_static and r.raw_scalar_display is not None and Decimal(2) <= r.raw_scalar_display <= Decimal(15)]
    charts.append(distribution('airflow', 'Calibrated scalar airflow', 'm/s', [(r.calibrated_velocity_m_s, r.csv_record_number) for r in eligible], len(records), ['M9 P3 linear calibration. AirDisplay domain 2–15 cm/s. Dynamic sequences, stalls, missing and out-of-domain observations excluded.']))
    return {'charts': charts, 'oxygen_quality': dict(Counter(r.category for r in oxygen)),
            'airflow_quality': dict(Counter(r.classification for r in airflow)),
            'morphology': dict(Counter(r.regime_code for r in morphology)),
            'specimens': [{'specimen': k, 'tests': v} for k, v in sorted(counts.items())],
            'unique_specimens': len(counts), 'repeated_specimens': sum(v > 1 for v in counts.values()),
            'pairs': [{'x': float(r.initial_o2_vol_pct / 100), 'y': float(r.final_o2_vol_pct / 100), 'row': r.csv_record_number, 'test': r.test_id} for r in oxygen if r.is_eligible_signed_cdf],
            'conditions': [{'test': m.test_id, 'row': m.csv_record_number, 'regime': m.regime_code, 'fuel': m.fuel_sample_material, 'specimen': m.sample_number, 'burn': m.burn_subset, 'oxygen': records[i].get(O2), 'airflow': records[i].get('Air display')} for i, m in enumerate(morphology)],
            'source': SOURCE, 'sha256': AUTHENTIC_SHA256,
            'notes': ['Repeated tests are not independent specimens.', 'Morphology categories do not establish universal ignition, extinction or flame-spread rules.', 'ISS observations do not establish lunar/Martian behaviour, spacecraft fire probability or crew survival.']}
