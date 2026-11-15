import pandas as pd

df = pd.read_csv('data/raw/bass_ii/original/PSI-25_Experimental table_BASS-II.csv')

# Track specimen sequence index
specimen_seen = {}
mapping_rows = []

for idx, row in df.iterrows():
    row_idx = idx + 2
    test_id = str(row['Test #']).strip()
    pi = str(row['PI']).strip()
    sample_no = str(row['Sample #']).strip()
    fuel = str(row['Fuel Sample Material']).strip()
    
    # Update specimen count
    specimen_seen[sample_no] = specimen_seen.get(sample_no, 0) + 1
    seq_idx = specimen_seen[sample_no]
    
    # Classify purely by observed categorical morphology & geometry (NO Biot number inference)
    if pi == 'Bhattacharjee':
        regime_code = 'THIN_PMMA_FILMS'
        regime_desc = 'Cast polymethyl methacrylate thin films (100 to 400 micron nominal thickness)'
        morph_category = 'OBSERVED_THIN_FILM_100_TO_400_MICRON'
        flow_geom = 'OPPOSED_FLOW'
    elif pi == 'Miller':
        morph_category = 'OBSERVED_THICK_SLAB_1_TO_5_MM'
        flow_geom = 'OPPOSED_FLOW'
        if '1 sided' in fuel.lower() or '1-sided' in fuel.lower():
            regime_code = 'THICK_PMMA_SLABS_1SIDED'
            regime_desc = 'Cast PMMA thick slabs (1 to 5 mm) 1-sided burn with phenolic mount conductive backing'
        elif '2 sided' in fuel.lower() or '2-sided' in fuel.lower():
            regime_code = 'THICK_PMMA_SLABS_2SIDED'
            regime_desc = 'Cast PMMA thick slabs (1 to 5 mm) 2-sided unbacked free burn'
        else:
            regime_code = 'THICK_PMMA_SLABS_UNSPECIFIED_MOUNT'
            regime_desc = 'Cast PMMA thick slabs (1 to 5 mm) mounting unspecified in CSV description'
    elif pi == 'Olson':
        regime_code = 'CLEAR_PMMA_RODS_STAGNATION'
        regime_desc = 'Clear cast PMMA cylindrical rods (1/4 in, 3/8 in, 1/2 in nominal diameter)'
        morph_category = 'OBSERVED_CYLINDRICAL_ROD_CLEAR'
        flow_geom = 'FORWARD_STAGNATION_CONCURRENT_FLOW'
    elif pi == 'Fernandez-Pello':
        regime_code = 'BLACK_PMMA_RODS_OPPOSED'
        regime_desc = 'Black carbon-doped PMMA cylindrical rods (1/4 in, 3/8 in, 1/2 in nominal diameter)'
        morph_category = 'OBSERVED_CYLINDRICAL_ROD_BLACK'
        flow_geom = 'OPPOSED_FLOW'
    elif pi == "T'ien":
        if 'sphere' in fuel.lower() or 'spherical' in fuel.lower():
            regime_code = 'PMMA_SPHERE_SEGMENT'
            regime_desc = 'Cast PMMA 4 cm spherical section exploratory geometry'
            morph_category = 'OBSERVED_CURVED_SPHERICAL_SEGMENT'
            flow_geom = 'FORCED_FLOW_OVER_SPHERE'
        else:
            regime_code = 'SIBAL_FABRIC_OPPOSED'
            regime_desc = 'SIBAL composite fabric (75% cotton / 25% fiberglass woven blend)'
            morph_category = 'OBSERVED_WOVEN_FABRIC_COMPOSITE'
            flow_geom = 'OPPOSED_FLOW'
    elif pi == 'Ferkul':
        if 'candle' in fuel.lower():
            regime_code = 'CANDLE_WAX_WICK'
            regime_desc = 'Japan Wax paraffin candle liquid melt pool with cotton wick'
            morph_category = 'OBSERVED_LIQUID_MELT_POOL_WICK'
            flow_geom = 'COFLOW_DIFFUSION'
        else:
            regime_code = 'NOMEX_III_FABRIC'
            regime_desc = 'Nomex III natural aramid inherently flame-resistant woven fabric'
            morph_category = 'OBSERVED_WOVEN_FABRIC_ARAMID'
            flow_geom = 'OPPOSED_FLOW'
    else:
        regime_code = 'UNKNOWN'
        regime_desc = 'Unknown'
        morph_category = 'UNKNOWN'
        flow_geom = 'UNKNOWN'
        
    mapping_rows.append({
        'source_row_index': row_idx,
        'test_id': test_id,
        'pi': pi,
        'sample_number': sample_no,
        'fuel_sample_material': fuel,
        'morphology_regime_code': regime_code,
        'morphology_regime_description': regime_desc,
        'observed_morphology_category': morph_category,
        'flow_geometry': flow_geom,
        'specimen_burn_sequence_index': seq_idx
    })

map_df = pd.DataFrame(mapping_rows)

# Determine total burns per sample
sample_totals = map_df['sample_number'].value_counts()
map_df['is_repeated_sample'] = map_df['sample_number'].map(lambda s: sample_totals[s] > 1)
map_df['repeated_sample_id_group'] = map_df['sample_number'].map(lambda s: s if sample_totals[s] > 1 else 'FIRST_BURN_SINGLE_RUN')
map_df['specimen_burn_subset'] = map_df['specimen_burn_sequence_index'].map(lambda idx: 'FIRST_BURN_SUBSET' if idx == 1 else 'SUBSEQUENT_REBURN_SUBSET')
map_df['sample_burn_confounder_notes'] = map_df.apply(
    lambda r: f'Repeated burn {r["specimen_burn_sequence_index"]} of {sample_totals[r["sample_number"]]}; potential confounding from thermal preheating, charring, and cumulative geometry regression' 
    if r['is_repeated_sample'] and r['specimen_burn_sequence_index'] > 1 
    else ('First burn of repeated specimen; virgin surface, but potential chamber accumulation dependence' if r['is_repeated_sample'] else 'Single-burn specimen; potential chamber accumulation dependence on same test day'),
    axis=1
)

final_cols = [
    'source_row_index', 'test_id', 'pi', 'sample_number', 'fuel_sample_material',
    'morphology_regime_code', 'morphology_regime_description', 'observed_morphology_category',
    'flow_geometry', 'specimen_burn_subset', 'is_repeated_sample', 'specimen_burn_sequence_index',
    'repeated_sample_id_group', 'sample_burn_confounder_notes'
]
map_df = map_df[final_cols]
map_df.to_csv('m9_p4_test_regime_mapping.csv', index=False)
print('Successfully regenerated m9_p4_test_regime_mapping.csv with rows:', len(map_df))
print(map_df['specimen_burn_subset'].value_counts())
