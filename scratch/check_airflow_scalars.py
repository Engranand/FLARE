import pandas as pd
import openpyxl

df = pd.read_csv('data/raw/bass_ii/original/PSI-25_Experimental table_BASS-II.csv')

# Find scalar Air display
scalar_rows = []
complex_rows = []
null_rows = []

for idx, r in df.iterrows():
    val = r['Air display']
    if pd.isna(val):
        null_rows.append(idx+2)
        continue
    s = str(val).strip()
    try:
        f = float(s)
        scalar_rows.append((idx+2, r['Test #'], r['PI'], r['Fuel Sample Material'], r['Flow restrictor'], str(r['Fan display']).strip(), s, f))
    except ValueError:
        complex_rows.append((idx+2, r['Test #'], str(val).strip()))

print(f'Total Air display: {len(df)}')
print(f'Null count: {len(null_rows)}')
print(f'Scalar count: {len(scalar_rows)}')
print(f'Complex sequence count: {len(complex_rows)}')

sdf = pd.DataFrame(scalar_rows, columns=['row', 'test_id', 'pi', 'fuel', 'flow_restr', 'fan_display', 'air_display_str', 'air_display_val'])

# Check calibration formula U = 1.0066 * Air display (cm/s)
sdf['u_cm_s'] = (1.0066 * sdf['air_display_val']).round(3)
sdf['u_m_s'] = (sdf['u_cm_s'] / 100.0).round(5)

# Check Fan display on scalar rows
def check_fan_limit(f_str):
    try:
        v = float(f_str)
        # Fan display is Volts * 10
        volts = v / 10.0 if v > 15 else v # some are entered as pot (e.g. 1.0) or voltage (e.g. 55 = 5.5V)
        return volts, volts >= 3.8
    except:
        return None, 'COMPLEX_FAN'

sdf['fan_volts_est'], sdf['fan_above_cutoff'] = zip(*sdf['fan_display'].apply(check_fan_limit))

print('\nAll 25 Scalar Records:')
print(sdf[['row', 'test_id', 'pi', 'flow_restr', 'fan_display', 'air_display_val', 'u_cm_s', 'u_m_s', 'fan_above_cutoff']].to_string())
