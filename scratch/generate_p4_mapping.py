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
    
    # Classify morphology
    if pi == 'Bhattacharjee':
        regime_code = 'THIN_PMMA_FILMS'
        regime_desc = 'Cast polymethyl methacrylate thin films (100 to 400 micron)'
        thermal_regime = 'THERMALLY_THIN_BI_LT_0_1'
        flow_geom = 'OPPOSED_FLOW'
    elif pi == 'Miller':
        thermal_regime = 'THERMALLY_THICK_BI_GT_1_0'
        flow_geom = 'OPPOSED_FLOW'
        if '1 sided' in fuel.lower() or '1-sided' in fuel.lower():
            regime_code = 'THICK_PMMA_SLABS_1SIDED'
            regime_desc = 'Cast PMMA thick slabs (1 to 5 mm) 1-sided burn with phenolic mount conductive loss'
        elif '2 sided' in fuel.lower() or '2-sided' in fuel.lower():
            regime_code = 'THICK_PMMA_SLABS_2SIDED'
            regime_desc = 'Cast PMMA thick slabs (1 to 5 mm) 2-sided unbacked free burn'
        else:
            regime_code = 'THICK_PMMA_SLABS_UNSPECIFIED_MOUNT'
            regime_desc = 'Cast PMMA thick slabs (1 to 5 mm) mounting unspecified in CSV description'
    elif pi == 'Olson':
        regime_code = 'CLEAR_PMMA_RODS_STAGNATION'
        regime_desc = 'Clear cast PMMA cylindrical rods (1/4 in, 3/8 in, 1/2 in diameter)'
        thermal_regime = 'THERMALLY_THICK_CYLINDER'
        flow_geom = 'FORWARD_STAGNATION_CONCURRENT_FLOW'
    elif pi == 'Fernandez-Pello':
        regime_code = 'BLACK_PMMA_RODS_OPPOSED'
        regime_desc = 'Black carbon-doped PMMA cylindrical rods (1/4 in, 3/8 in, 1/2 in diameter)'
        thermal_regime = 'THERMALLY_THICK_CYLINDER'
        flow_geom = 'OPPOSED_FLOW'
    elif pi == "T'ien":
        if 'sphere' in fuel.lower() or 'spherical' in fuel.lower():
            regime_code = 'PMMA_SPHERE_SEGMENT'
            regime_desc = 'Cast PMMA 4 cm spherical section exploratory geometry'
            thermal_regime = 'THREE_DIMENSIONAL_CURVED'
            flow_geom = 'FORCED_FLOW_OVER_SPHERE'
        else:
            regime_code = 'SIBAL_FABRIC_OPPOSED'
            regime_desc = 'SIBAL composite fabric (75% cotton / 25% fiberglass blend)'
            thermal_regime = 'POROUS_COMPOSITE_THERMALLY_THIN'
            flow_geom = 'OPPOSED_FLOW'
    elif pi == 'Ferkul':
        if 'candle' in fuel.lower():
            regime_code = 'CANDLE_WAX_WICK'
            regime_desc = 'Japan Wax paraffin candle liquid melt pool with cotton wick'
            thermal_regime = 'LIQUID_MELT_POOL_WICK'
            flow_geom = 'COFLOW_DIFFUSION'
        else:
            regime_code = 'NOMEX_III_FABRIC'
            regime_desc = 'Nomex III natural aramid inherently flame-resistant woven fabric'
            thermal_regime = 'ARAMID_FABRIC_THERMALLY_THIN'
            flow_geom = 'OPPOSED_FLOW'
    else:
        regime_code = 'UNKNOWN'
        regime_desc = 'Unknown'
        thermal_regime = 'UNKNOWN'
        flow_geom = 'UNKNOWN'
        
    mapping_rows.append({
        'source_row_index': row_idx,
        'test_id': test_id,
        'pi': pi,
        'sample_number': sample_no,
        'fuel_sample_material': fuel,
        'morphology_regime_code': regime_code,
        'morphology_regime_description': regime_desc,
        'thermal_thickness_regime': thermal_regime,
        'flow_geometry': flow_geom,
        'specimen_burn_sequence_index': seq_idx
    })

map_df = pd.DataFrame(mapping_rows)

# Determine total burns per sample
sample_totals = map_df['sample_number'].value_counts()
map_df['is_repeated_sample'] = map_df['sample_number'].map(lambda s: sample_totals[s] > 1)
map_df['repeated_sample_id_group'] = map_df['sample_number'].map(lambda s: s if sample_totals[s] > 1 else 'VIRGIN_SINGLE_BURN')
map_df['sample_burn_confounder_notes'] = map_df.apply(
    lambda r: f'Repeated burn {r["specimen_burn_sequence_index"]} of {sample_totals[r["sample_number"]]}; specimen thermal preheating and charring confounder present' 
    if r['is_repeated_sample'] else 'Virgin specimen; uncharred initial state',
    axis=1
)

# Reorder columns
final_cols = [
    'source_row_index', 'test_id', 'pi', 'sample_number', 'fuel_sample_material',
    'morphology_regime_code', 'morphology_regime_description', 'thermal_thickness_regime',
    'flow_geometry', 'is_repeated_sample', 'specimen_burn_sequence_index',
    'repeated_sample_id_group', 'sample_burn_confounder_notes'
]
map_df = map_df[final_cols]
map_df.to_csv('m9_p4_test_regime_mapping.csv', index=False)
print('Successfully generated m9_p4_test_regime_mapping.csv with rows:', len(map_df))
