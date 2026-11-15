import pandas as pd

df = pd.read_csv('data/raw/bass_ii/original/PSI-25_Experimental table_BASS-II.csv')

p3_rows = []

for idx, row in df.iterrows():
    row_idx = idx + 2
    test_id = str(row['Test #']).strip()
    pi = str(row['PI']).strip()
    flow_restr = str(row['Flow restrictor']).strip()
    fan_raw = str(row['Fan display']).strip() if pd.notna(row['Fan display']) else 'NULL'
    air_raw = str(row['Air display']).strip() if pd.notna(row['Air display']) else 'NULL'
    
    # Restrictor valid range
    if flow_restr == '0':
        restr_range = '0.0 to 29.2 cm/s (unrestricted duct)'
    elif flow_restr == '1':
        restr_range = '0.0 to 21.1 cm/s (1 restrictor plate)'
    elif flow_restr == '2':
        restr_range = '0.0 to 18.1 cm/s (2 restrictor plates)'
    else:
        restr_range = 'Unspecified restrictor geometry'
        
    # Check airflow classification
    if air_raw == 'NULL' or air_raw.lower() in ['', 'nan', 'none']:
        classification = 'MISSING_AIRFLOW'
        validity = 'MISSING_EXCLUDED'
        u_cm = None
        u_m = None
        formula = 'NONE'
        notes = 'Air display missing or unrecorded in flight telemetry'
    else:
        try:
            air_val = float(air_raw)
            classification = 'STATIC_SCALAR_FLOW'
            formula = 'U = 1.0066 * (Air Display) [cm/s]'
            u_cm = round(1.0066 * air_val, 3)
            u_m = round(u_cm / 100.0, 5)
            
            # Check motor stall cutoff (air_display == 0.0 or fan voltage <= 3.8V)
            if air_val == 0.0:
                validity = 'MOTOR_STALL_DEADBAND'
                notes = 'Air display is 0.0; fan operates at zero flow or in motor stall deadband (<3.8V); excluded from velocity regressions'
            else:
                validity = 'VALID_CALIBRATED_STEADY_FLOW'
                notes = f'Valid steady-state centerline velocity within empirical calibration limit for restrictor {flow_restr}'
        except ValueError:
            classification = 'DYNAMIC_FLOW_SEQUENCE'
            validity = 'SEQUENCE_EXCLUDED_FROM_STATIC_MAPPING'
            u_cm = None
            u_m = None
            formula = 'NONE_DYNAMIC_SEQUENCE'
            notes = 'Contains multi-step fan adjustment sequence or embedded operator text notes; valid for transient analysis only, excluded from static velocity mapping'
            
    p3_rows.append({
        'source_row_index': row_idx,
        'test_id': test_id,
        'pi': pi,
        'flow_restrictor_setting': flow_restr,
        'fan_display_raw': fan_raw,
        'air_display_raw': air_raw,
        'airflow_classification': classification,
        'calibrated_velocity_cm_s': u_cm,
        'calibrated_velocity_m_s': u_m,
        'calibration_validity_status': validity,
        'valid_restrictor_range_cm_s': restr_range,
        'calibration_formula_applied': formula,
        'operating_limit_notes': notes
    })

p3_df = pd.DataFrame(p3_rows)
p3_df.to_csv('m9_p3_calibration_eligibility.csv', index=False)
print('Successfully generated m9_p3_calibration_eligibility.csv with rows:', len(p3_df))
print(p3_df['calibration_validity_status'].value_counts())
