import pandas as pd

df = pd.read_csv('data/raw/bass_ii/original/PSI-25_Experimental table_BASS-II.csv')

c_init = 'Calibrated  initial O2 % by vol '
c_final = 'Calibrated final O2 % by vol'

rows = []

for idx, r in df.iterrows():
    row_idx = idx + 2
    test_id = str(r['Test #']).strip()
    pi = str(r['PI']).strip()
    fuel = str(r['Fuel Sample Material']).strip()
    i_str = str(r[c_init]).strip()
    f_str = str(r[c_final]).strip()
    
    if f_str.lower() in ['none', 'nan', '']:
        rows.append({
            'source_row_index': row_idx,
            'test_id': test_id,
            'pi': pi,
            'fuel_sample_material': fuel,
            'initial_o2_vol_pct': i_str,
            'final_o2_vol_pct': f_str,
            'delta_o2_vol_pct': 'NULL',
            'delta_o2_mole_fraction': 'NULL',
            'p2_eligibility_category': 'MISSING_FINAL_O2',
            'depletion_regime': 'UNRECORDED',
            'eligible_for_standard_aggregations': False,
            'eligible_for_signed_distribution': False,
            'quarantine_or_exclusion_reason': 'MISSING_FINAL_MEASUREMENT_TOKEN_NONE'
        })
        continue
        
    try:
        i_val = float(i_str)
        f_val = float(f_str)
        delta = round(i_val - f_val, 4)
        delta_si = round(delta / 100.0, 6)
        
        if delta > 5.0 or delta < -0.2:
            cat = 'QUARANTINED_GROSS_ANOMALY'
            regime = 'GROSS_ANOMALY'
            std_elig = False
            sgn_elig = False
            reason = 'GROSS_RECORDING_ANOMALY_DELTA_EXCEEDS_PHYSICAL_LIMIT'
        elif delta < 0.0:
            cat = 'NEGATIVE_SENSOR_DRIFT'
            regime = 'NEGATIVE_DRIFT'
            std_elig = False
            sgn_elig = True
            reason = 'SENSOR_RESOLUTION_LIMIT_NEGATIVE_DRIFT_PRESERVED_SIGNED'
        elif delta == 0.0:
            cat = 'NON_NEGATIVE_DEPLETION'
            regime = 'ZERO_DEPLETION'
            std_elig = True
            sgn_elig = True
            reason = 'NONE_VALID_MEASUREMENT'
        else:
            cat = 'NON_NEGATIVE_DEPLETION'
            regime = 'POSITIVE_DEPLETION'
            std_elig = True
            sgn_elig = True
            reason = 'NONE_VALID_MEASUREMENT'
            
        rows.append({
            'source_row_index': row_idx,
            'test_id': test_id,
            'pi': pi,
            'fuel_sample_material': fuel,
            'initial_o2_vol_pct': str(i_val),
            'final_o2_vol_pct': str(f_val),
            'delta_o2_vol_pct': str(delta),
            'delta_o2_mole_fraction': str(delta_si),
            'p2_eligibility_category': cat,
            'depletion_regime': regime,
            'eligible_for_standard_aggregations': std_elig,
            'eligible_for_signed_distribution': sgn_elig,
            'quarantine_or_exclusion_reason': reason
        })
    except Exception as e:
        rows.append({
            'source_row_index': row_idx,
            'test_id': test_id,
            'pi': pi,
            'fuel_sample_material': fuel,
            'initial_o2_vol_pct': i_str,
            'final_o2_vol_pct': f_str,
            'delta_o2_vol_pct': 'NULL',
            'delta_o2_mole_fraction': 'NULL',
            'p2_eligibility_category': 'PARSE_ERROR',
            'depletion_regime': 'ERROR',
            'eligible_for_standard_aggregations': False,
            'eligible_for_signed_distribution': False,
            'quarantine_or_exclusion_reason': str(e)
        })

out_df = pd.DataFrame(rows)
out_df.to_csv('m9_p2_record_eligibility.csv', index=False)
print('Regenerated m9_p2_record_eligibility.csv with rows:', len(out_df))
print(out_df['depletion_regime'].value_counts())
