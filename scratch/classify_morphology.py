import pandas as pd

df = pd.read_csv('data/raw/bass_ii/original/PSI-25_Experimental table_BASS-II.csv')

def classify_morphology(row):
    pi = row['PI']
    fuel = str(row['Fuel Sample Material']).strip()
    
    if pi == 'Bhattacharjee':
        return 'THIN_PMMA_FILMS', 'Thermally thin flat PMMA films (100-400 um) in opposed flow'
    elif pi == 'Miller':
        if '1 sided' in fuel.lower() or '1-sided' in fuel.lower():
            return 'THICK_PMMA_SLABS_1SIDED', 'Thermally thick PMMA slabs (1-5 mm) with 1-sided burn'
        elif '2 sided' in fuel.lower() or '2-sided' in fuel.lower():
            return 'THICK_PMMA_SLABS_2SIDED', 'Thermally thick PMMA slabs (1-5 mm) with 2-sided unbacked free burn'
        else:
            return 'THICK_PMMA_SLABS_UNSPECIFIED_MOUNT', 'Thermally thick PMMA slabs (1-5 mm) unspecified mounting'
    elif pi == 'Olson':
        return 'CLEAR_PMMA_RODS_STAGNATION', 'Clear cast PMMA cylindrical rods (1/4 in, 3/8 in, 1/2 in) in forward stagnation flow'
    elif pi == 'Fernandez-Pello':
        return 'BLACK_PMMA_RODS_OPPOSED', 'Black carbon-doped PMMA cylindrical rods (1/4 in, 3/8 in, 1/2 in) in opposed flow'
    elif pi == "T'ien":
        if 'sphere' in fuel.lower() or 'spherical' in fuel.lower():
            return 'PMMA_SPHERE_SEGMENT', 'PMMA 4 cm spherical section exploratory geometry'
        else:
            return 'SIBAL_FABRIC_OPPOSED', 'Cotton-fiberglass composite fabric (75/25 blend) in opposed flow'
    elif pi == 'Ferkul':
        if 'candle' in fuel.lower():
            return 'CANDLE_WAX_WICK', 'Paraffin/Japan Wax candle liquid melt pool diffusion flame'
        else:
            return 'NOMEX_III_FABRIC', 'Nomex III aramid inherently flame-resistant fabric'
    return 'UNKNOWN', 'Unknown material'

df['regime_code'], df['regime_desc'] = zip(*df.apply(classify_morphology, axis=1))

print('Morphology Breakdown:')
print(df['regime_code'].value_counts())
print('\nPI Breakdown:')
print(df['PI'].value_counts())

# Repeated sample breakdown
sample_counts = df['Sample #'].value_counts()
repeated_samples = sample_counts[sample_counts > 1]
print(f'\nRepeated samples count: {len(repeated_samples)} specimens involved in {repeated_samples.sum()} runs')
for s, c in repeated_samples.items():
    tests = df[df['Sample #'] == s]['Test #'].tolist()
    pi_val = df[df['Sample #'] == s]['PI'].iloc[0]
    fuel_val = df[df['Sample #'] == s]['Fuel Sample Material'].iloc[0]
    print(f'  Sample #{s} (N={c}): Tests={tests}, PI={pi_val}, Fuel={fuel_val}')
