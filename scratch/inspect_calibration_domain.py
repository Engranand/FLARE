import openpyxl

wb = openpyxl.load_workbook('data/raw/challenge_resources/original/bass_ii/PSI-25_Reference Data_Fan calibration data.xlsx', data_only=True)
ws = wb['Fan Calibration data']

print(f'Sheet max_row={ws.max_row}, max_col={ws.max_column}')

# Check Row 1 note
print('\nRow 1 Note:')
print(ws.cell(1, 4).value)

# Check footnotes
for r in range(32, 36):
    row_vals = [f'C{c}: {ws.cell(r, c).value}' for c in range(1, 15) if ws.cell(r, c).value is not None]
    if row_vals:
        print(f'Row {r}:', ' | '.join(row_vals))

# Find all calibration blocks across columns
cal_blocks = []
for c in range(1, ws.max_column + 1):
    val = ws.cell(3, c).value
    if val is not None and 'DATE' in str(val).upper():
        date_val = str(ws.cell(3, c+1).value)
        gmt_val = str(ws.cell(4, c+1).value)
        cal_blocks.append((c, date_val, gmt_val))

print(f'\nFound {len(cal_blocks)} calibration date blocks')

# Check Air Display values across all calibration blocks
air_vals_by_restr = {0: [], 1: [], 2: [], 'unknown': []}

for col_idx, d, g in cal_blocks:
    # Look for restrictor sections in this block
    # Standard block has rows 6-13 for no restrictor, 14-21 for 1 restrictor, 23-31 for 2 restrictors
    # Or check text in col_idx+3
    for r in range(7, 32):
        # find air display column
        # In first block, Air Display is col 3
        # Check header in row 6
        for c in range(col_idx, col_idx + 4):
            header = str(ws.cell(6, c).value).lower() if ws.cell(6, c).value else ''
            if 'air' in header:
                val = ws.cell(r, c).value
                if val is not None:
                    try:
                        f = float(val)
                        if r <= 13:
                            air_vals_by_restr[0].append((d, g, f))
                        elif r <= 21:
                            air_vals_by_restr[1].append((d, g, f))
                        else:
                            air_vals_by_restr[2].append((d, g, f))
                    except:
                        pass

for r_code, vals in air_vals_by_restr.items():
    if vals:
        nums = [v[2] for v in vals]
        print(f'Restrictor {r_code}: count={len(nums)}, min={min(nums)}, max={max(nums)}, unique={sorted(set(nums))}')
