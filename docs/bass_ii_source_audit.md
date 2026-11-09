# BASS-II source audit — Milestone 2A

Audit date: **2026-11-05 (Asia/Calcutta)**. Scope: source discovery and documentation only; no ingestion pipeline, application changes, or scientific validation.

## Evidence and verification scope

Primary source: [NASA PSI-25](https://psi.nasa.gov/physci/repo/data/investigations/PSI-25), live browser inspection, Version 4. The ordinary web text reader returned an empty page; the JavaScript-enabled browser rendered metadata, table contents and file listings successfully. Search-index text was used for discovery, not as the sole basis for the experimental values below.

**Verified** means observed in the live NASA interface, with the verification scope stated. It does not mean physically validated, independently reproduced, or checked against instrument output. **Unverified** means the relevant content or interpretation was not accessible or established. No original binary/CSV download was successfully captured, hashed or parsed. The experimental CSV was inspected through NASA's own rendered table. Whitespace in human-readable tables below is collapsed for readability; values, qualifiers and missingness are not changed. Original file bytes remain to be acquired in Milestone 2B.

The table reports **130 rows**. Inspection of both pages at 100 rows/page found **129 nonblank rows with test IDs and one all-blank row at displayed position 130**. Do not report 130 experiments. All displayed rows were checked for structure, blank/literal-none cells, duplicate identifiers and selected annotation patterns; ten records B1–B10 are documented field by field below. This is not a claim that all 129 records have been scientifically reviewed. No associated Modeling Table is shown.

## Investigation metadata observed

| Field | Live source value / location |
| --- | --- |
| Investigation | Burning and Suppression of Solids - II(BASS-II), page heading |
| Identifier | PSI-25 |
| DOI | 10.60555/4qc4-de67, DOI link |
| Version | 4; Version History says updated 24-Nov-2025, Metadata update |
| Submitted / initial release | 31-Dec-2022 / 31-Dec-2022 |
| Platform | International Space Station (ISS), Description → Project |
| Project type | Microgravity Investigation |
| Investigation dates | 01-01-2010 through 12-31-2022 (metadata dates, not individual test dates) |
| Agency / center | NASA / Glenn Research Center (GRC) |
| Research area / subarea | Combustion Science / Spacecraft Fire Safety |
| Related investigation | PSI-26; not merged with PSI-25 |
| Hardware | Microgravity Science Glovebox (MSG) |
| Displayed total size | 255.77 GB; portal-reported, not independently summed |
| License label | CC0-1.0, linked from investigation header |

Version history lists 694 additions and 131 removals for Version 4. These are change-event counts, not a verified current inventory total. Several inspected file entries show 25-Nov-2025 while version metadata says 24-Nov-2025; retain both fields without silently reconciling them.

## Content-inspected dataset inventory

Only the following file's experimental content was actually inspected. Other files are listed separately as discovery leads, not content-verified inventory entries.

| File name | File format | Data category | Investigation ID | Experimental variables | Access method | Source URL | Verification status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PSI-25_Experimental table_BASS-II.csv | CSV as named by NASA; encoding/dialect not byte-verified | Experimental table | PSI-25 | 17 columns: identity/date/sample/material; restrictor, fan/air displays, radiometer gain, frame count; initial/final O2, CO2, CO | Public investigation page → Experimental Table → select this filename; pagination and Filter work. Data files and documents → Experimental table folder also lists it | [NASA PSI-25](https://psi.nasa.gov/physci/repo/data/investigations/PSI-25) | **Verified: rendered content and listing only. Unverified: downloaded bytes, checksum, CSV quoting/encoding** |

The file listing reports **16.2 KB**, date added **Thu Feb 06 2025**. That is portal metadata, not a measured local file size.

## Access mechanism actually observed

1. Open the public investigation page in a JavaScript-enabled browser; no sign-in was requested for metadata/table/file-tree access.
2. Experimental Table exposes a filename selector, text filter, and page-size options 5, 10, 25 and 100. At 100, the two pages show positions 1–100 and 101–130.
3. Under Data files and documents, click the **folder icon** to expand directories. Clicking the row/name selects an item; it is not a direct file hyperlink. A Download button appears for selection; a Download Zip control was also observed with multiple selected items. Check the selection count to avoid requesting a whole large directory.
4. Selecting only the CSV and pressing Download was attempted. No capturable download resulted; the browser download-event wait timed out. Successful byte retrieval is **not verified**, and this does not prove the source is unavailable to other clients.
5. PDF/MP4 entries expose Preview buttons. The SRD PDF Preview opened a dialog with an iframe and an empty accessible document. Its DOM source was an expiring signed S3 URL at host `psi-curation-prod.s3.amazonaws.com`, object path `/legacy/Filestreamdb/10767/SRD_BASS-II.pdf`, with attachment filename `SRD_BASS-II.pdf`. This establishes the observed preview mechanism and an alias of the portal filename, not a public API contract. Signed query parameters are intentionally not stored here. The unsigned object URL was not accessible through the web reader.
6. The Read Me → Files control was tried but did not expose readable supporting content in this session. No authentication requirement for actual downloads has been established.

**No NASA API endpoint was discovered or invented.** Do not construct download URLs from filenames, object IDs or neighboring files. Re-obtain authorized links through the official UI; do not hardcode temporary signatures. No bulk download of the 255.77 GB investigation was attempted.

## Discovery leads — listing inspected, file contents unverified

All filenames below were observed in the live file tree unless otherwise stated. They are not added to the content-inspected inventory. Formats are filename extensions, not validated MIME types. Source for every entry is the [NASA file tree](https://psi.nasa.gov/physci/repo/data/investigations/PSI-25).

| Directory | Exact listed filename | Displayed size | Content/access status |
| --- | --- | --- | --- |
| Science Documents | PSI-25_Science Documents_BASS-II_Test.Matrices.xlsx | 28.28 KB | Listing only; sheets, headers and values unverified |
| Science Documents | PSI-25_Science Documents_BASS-II_ReadMe.docx | 21.03 KB | Listing only; instructions unverified |
| Science Documents | PSI-25_Science Documents_BASS-II_SRD.pdf | 1.06 MB | Preview dialog inspected; document pages unreadable |
| Engineering Documents | PSI-25_Engineering Documents_BASS-II_Engineering Requirements.pptx | 1.07 MB | Listing only |
| Engineering Documents | PSI-25_Engineering Documents_BASS-II_Ops.docx | 1.06 MB | Listing only |
| Reports | PSI-25_Reports_BASS-II Summary Report.pdf | 46.7 MB | Listing only; no report findings extracted |
| Raw Data → Reduced Gravity → Bhattacharjee → B1 | PSI-25_Raw Data_BASS_GMT50_SAMPLE_147_TEST_B1.mp4 | 5.54 MB | Listing and Preview control only; video not analyzed |
| Same B1 directory | PSI-25_Raw Data_BASS_GMT50_SAMPLE_147_TEST_B1_Still_Sequence.mp4 | 2.7 MB | Listing only |
| Same B1 directory | PSI-25_Raw Data_iss038e051108.zip | 627.61 MB | Listing only; archive members unknown |
| Same B1 directory | PSI-25_Raw Data_BASS_GMT50_SAMPLE_148_TEST_B3.mp4 | 7.63 MB | Listing only; B3 filename in B1 folder is an unresolved association issue |
| Same B1 directory | PSI-25_Raw Data_GMT2014_050_BASS_S147M_TPB1_ProofSheet.pdf | 258.21 KB | Listing only |
| Same B1 directory | PSI-25_Raw Data_BASS_GMT50_SAMPLE_147_TEST_B1 original videos.zip | 13.96 MB | Listing only; archive members unknown |

These entries show Tue Nov 25 2025 as date added. Raw Data → Reduced Gravity contains investigator folders Bhattacharjee, Ferkul, Fernandez-Pello, Miller, Olson and T'ien. Only the B1 subtree was expanded to file level. Reference Data showed no children during the attempted inspection; do not infer that no reference data exists. The representative-image section labels `PSI-25_Representative Image(s)_BASS-II_flame testing.jpg`; image content was not analyzed. The metadata ZIP filename was seen only in version history, not inspected as an archive.

## Ten representative records, source-verified transcription

Source for **every cell below**: [PSI-25](https://psi.nasa.gov/physci/repo/data/investigations/PSI-25) → Experimental Table → `PSI-25_Experimental table_BASS-II.csv`, Version 4, no filter, initial source ordering. Positions are **displayed data rows excluding the header**, not asserted physical CSV line numbers. At page size 10 these are page 1, rows 1–10. Column names are in the dictionary. Verification is against the NASA-rendered table only.

All ten have PI `Bhattacharjee`. `⟦blank⟧` is this report's notation for an empty source cell, not a NASA token. `none` is literal source text. Variables not represented in these columns must not be inferred from a paper or another test.

| Source row | Test # | Date (original) | GMT | Sample # | Fuel Sample Material (display text) |
| --- | --- | --- | --- | --- | --- |
| 1 | B1 | 2/19/2014 | 50 | 147 | 100 micron PMMA film 2 cm wide |
| 2 | B2 | 2/19/2014 | 50 | 155 | 200 micron PMMA film 2 cm wide |
| 3 | B3 | 2/19/2014 | 50 | 148 | 100 micron film 2 cm wide |
| 4 | B4 | 2/19/2014 | 50 | 159 | 300 micron PMMA film 2 cm wide |
| 5 | B5 | 2/19/2014 | 50 | 156 | 200 micron 2 cm wide |
| 6 | B6 | 7/7/2014 | 188 | 153m | 2 cm 0.1 mm PMMA film |
| 7 | B7 | 2/19/2014 | 50 | 161 | 400 micron film 2 cm wide |
| 8 | B8 | 7/7/2014 | 188 | 157m | 2 cm 0.2 mm PMMA film |
| 9 | B9 | 7/7/2014 | 188 | 154m | 2 cm 0.1 mm PMMA film |
| 10 | B10 | 7/7/2014 | 188 | 173m | 1 cm 0.2 mm PMMA film |

| Test # | Flow restrictor | Fan display | Air display | Radiometer gain (1000 250 50 10) | Total Frames Shot |
| --- | --- | --- | --- | --- | --- |
| B1 | 2 | 62 | 5 | 50 | 57 |
| B2 | 2 | 62 | 5 | 50 | none |
| B3 | 2 | 47 | 2 | 50 | 253 |
| B4 | 2 | 61 | 5 | 50 | 137 |
| B5 | 2 | 59 | 5 | 50 | 206 |
| B6 | 2 | 0.9 1.3 2.75 | 3 5 approaching 10 | 10 | 80 |
| B7 | 2 | 47 | 2 | 50 | 84 |
| B8 | 0 | 1.4 incr to 10.0 | 10 max | 10 | 226 |
| B9 | 2 | 0.6 0.35 | 2 <1 | 10 | 45 |
| B10 | 2 | 1.7 (52) 1.25 0.9 0.6 0.4 0.35 | 5 4 3 2 1 | 10 | 123 |

Do not assign physical units to those settings from their magnitudes. Frame count is a count, not a frame rate or elapsed time.

| Test # | Calibrated initial O2 (% by vol) | Calibrated final O2 (% by vol) | Initial CO2 (% by vol) | Final CO2 (% by vol) | Initial CO (ppm) | Final CO (ppm) | Missing cells / markers |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B1 | 22.2 | 22.2 | 0.44 | 0.44 | 0 | 6 | None in the 17 displayed columns |
| B2 | 22.2 | 1.6 | 0.44 | ⟦blank⟧ | 6 | ⟦blank⟧ | Final CO2 and final CO blank; Total Frames Shot = literal none |
| B3 | 22.2 | 21.8 | 0.43 | 0.49 | 12 | 19 | None in displayed columns |
| B4 | 22.2 | 22.2 | 0.44 | 0.51 | -1 | 10 | No blank; negative value retained |
| B5 | 22.2 | 21.9 | 0.43 | 0.43 | 0 | 12 | None in displayed columns |
| B6 | 21 | 20.9 | 0.33 | 0.41 | 0 | 0.3 | None in displayed columns |
| B7 | 22.2 | 22.1 | 0.45 | 0.51 | 1 | 17 | None in displayed columns |
| B8 | 21 | 20.5 | 0.33 | 0.58 | 0 | 131 | None in displayed columns |
| B9 | 21 | 20.9 | 0.33 | 0.35 | 0 | 10 | None in displayed columns |
| B10 | 21 | 20.8 | 0.33 | 0.44 | 0 | 23 | None in displayed columns |

These are recorded readings, not independently validated measurements. B3/B5/B7 do not explicitly identify PMMA in their material cells; do not fill it from neighbors. No dedicated flow-direction, ignition-duration/power, flame-spread-rate or extinction-limit columns exist in this table.

## Scientific data quality findings

### Missingness audit of the rendered table

Counts below exclude all-blank position 130 and cover the 129 identified rows. Comparison used trimmed DOM cell text; original CSV whitespace/quoting has not been verified.

| Column | Empty cells | Literal none cells |
| --- | ---: | ---: |
| Fan display | 13 | 0 |
| Air display | 4 | 0 |
| Total Frames Shot | 0 | 1 |
| Calibrated final O2 % by vol | 0 | 2 |
| Initial CO2 % by vol | 0 | 2 |
| Final CO2 % by vol | 1 | 5 |
| Initial CO (ppm) | 0 | 2 |
| Final CO (ppm) | 1 | 4 |

Other columns had no empty or literal-none cells among the 129 identified rows. This does not establish semantic completeness: qualifiers, malformed text and undefined units remain. `0` must remain a reported zero, distinct from blank, none, unknown, and not represented in this table.

### Specific issues and exact locations

| Issue | Source row/test/column | Required treatment |
| --- | --- | --- |
| Negative reading | Row 4 B4, Initial CO (ppm) = -1; also later rows | Preserve and flag; do not clamp to zero or presume an error code |
| Large O2 changes / unusual values | Row 2 B2 final O2 = 1.6; row 96 P22a = 0.6; row 97 P22b = 39.1; row 127 T28a = 0.9; row 128 T28b = 40.4 (% by vol) | Recorded values verified; interpretation unresolved. Check source matrix/calibration before comparison, not automatic correction |
| Censoring / undefined tokens | Row 31 M5 final CO = >500; row 51 O4 final CO = OR; row 61 O12 initial/final CO = OR; row 63 O13b final CO = over | Preserve exact tokens and units. >500 is a bound, not 500; OR/over meanings require documentation |
| Compound flow settings | B6/B8/B9/B10; row 79 P5 Fan display includes Fan pot 1.5 (5cm/s) and a sequence ending 0 ext | Do not average, use first number, or fabricate timestamps; preserve complete ordered text |
| Mixed geometry notation | micron, mm, cm; rod text such as quoted 3/8 and 0.5 with quote characters | Keep original strings; inch interpretation and geometry roles need confirmation. No silent unit conversion |
| Material/geometry ambiguity | B3/B5/B7 omit material; slab descriptions mix width/thickness and side counts; observed typos include 2ide and blac | Keep raw descriptions and unresolved fields; no neighbor-based filling |
| Ignition annotations | Row 41 M15 Fan display begins ignited 10; row 122 T23 material includes moved igniter; row 123 T24 includes top side ign | Qualitative annotations, not measured ignition power/duration |
| Extinction annotations | Row 79 P5 and other settings contain ext; test O8a Fan display explicitly contains extinguished | Retain text as an annotation; no numeric extinction threshold without calibration and timing |
| Date anomalies | Rows 108 T9 and 117 T18 show 6/24/2018, unlike nearby 2014 dates | Preserve 2018; verify against original logs, do not change to 2014 |
| Reused samples / suffixes | P22a/P22b both sample 200m; T28a/T28b both 144m | Distinct tests; do not deduplicate by sample or strip a/b suffixes |
| Cross-file association | B1 raw-data directory includes a filename identifying B3/sample 148 | Directory alone cannot establish test membership; resolve before joining media |
| Version/filename ambiguity | SRD portal filename differs from signed object's attachment filename | Keep both aliases and source path, not a guessed renamed file |

No duplicate nonempty Test # strings or identical complete nonblank rows were found among the 129 rendered rows. This does not rule out duplicated physical runs, copied media, or duplicates across archives/versions. Tests are not necessarily independent replicates.

### Comparison limitations

Fuel, dimensions, coatings/appearance, exposure sides, oxygen concentration, flow restrictor, fan setting sequence, radiometer gain and ignition placement vary. Initial/final gas readings do not establish constant conditions or a time series. The general project description mentions opposed and concurrent flows, but per-record flow direction is not a table column. Geometry and unit ambiguities prevent trustworthy cross-test flow/flammability comparisons until documentation is read. No uncertainty, instrument calibration coefficients, sample pressure or temperature columns were identified. Do not infer uncertainty or causal effects from this audit.

## Documentation, publications, licensing and attribution

The investigation header labels the collection **CC0-1.0** and links to [the license text](https://spdx.org/licenses/CC0-1.0.html). This is a verified portal label, not a legal review of every linked third-party publication. Check file-specific notices when bytes become accessible; do not assume publisher PDFs have the same rights.

The [PSI repository notice](https://psi.nasa.gov/physci/repo) requires citation of publicly available NASA-funded data/software using persistent identifiers. The live **Cite this Investigation** control displayed this citation (spelling preserved):

> Ferkul P, Fernandez-Pello C, Miller F, T'ien J, Bhattachjee S. "Burning and Suppression of Solids - II(BASS-II)", NASA PSI Data Repository, Version 4, http://doi.org/10.60555/4qc4-de67

BibTex and RIS download controls are offered; those exports were not captured. Cite DOI and version, retain the access date and file provenance. CC0 labeling and NASA's requested scholarly attribution are recorded separately.

The live Publications section lists 17 entries. These are bibliographic metadata only; their statements were not used as experimental measurements. DOI-linked entries observed include:

| Publication topic/title | Listed DOI |
| --- | --- |
| Microgravity flammability boundary for PMMA rods in axial stagnation flow: Experimental results and energy balance analyses | 10.1016/j.combustflame.2017.03.001 |
| Temperature and CO2 fields of a downward spreading flame over thin cellulose: A comparison of experimental and computational results | 10.1016/j.proci.2014.05.093 |
| Opposed-flow flame spread: A comparison of microgravity and normal gravity experiments to establish the thermal regime | 10.1016/j.firesaf.2015.11.011 |
| The critical flow velocity for radiative extinction in opposed-flow flame spread in a microgravity environment | 10.1016/j.combustflame.2015.10.023 |
| Experimental validation of a correlation capturing the boundary layer effect on spread rate in the kinetic regime of opposed-flow flame spread | 10.1016/j.proci.2014.06.125 |
| Radiative, thermal, and kinetic regimes of opposed-flow flame spread | 10.1016/j.proci.2016.06.025 |
| Concurrent flame growth, spread, and quenching over composite fabric samples in low speed purely forced flow in microgravity | 10.1016/j.proci.2016.06.028 |
| A Study of the Effectiveness of a Narrow Channel Apparatus in Simulating Microgravity Flame Spread over Thin Fuels | 10.2514/6.2012-3493 |
| Fire in Microgravity | 10.1511/2016.118.44 |

Other listed entries include the BASS-II Summary Report (Marcum, Olson, Ferkul), the on-board CSA-CP/CDM sensor report, PMMA sheet modeling, composite fabric growth/extinction, mixed-convection blowoff comparisons, PMMA rods in concurrent flow, narrow-channel intermediate-fuel work, and the MSG fire-safety investigation. DOI absence in this display does not establish that no DOI exists.

## Remaining uncertainties and decision

Byte-level CSV shape, XLSX sheets, full README/SRD/operations guidance, calibration and token definitions, archive contents, individual media attribution, file-specific notices and successful downloads remain unverified. The ten-record requirement is met at **rendered-source transcription level**, not raw-file validation level. The schema can now be grounded in actual observed columns, but ingestion must begin with acquisition and reconciliation, not with unreviewed numerical assumptions.

See [data dictionary](bass_ii_data_dictionary.md) and [Milestone 2B plan](bass_ii_ingestion_plan.md). Stop after review of these documents; no ingestion implementation has been added.
