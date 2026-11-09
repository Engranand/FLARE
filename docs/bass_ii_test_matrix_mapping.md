# BASS-II workbook-to-CSV mapping — M2B-2R

Sources throughout: CSV = `PSI-25_Experimental table_BASS-II.csv`; FAQ = `BASS-II data FAQ.docx`; workbook = `BASS-II Test Matrix by PI Final.xlsx`. These shorthand names always refer to the immutable files in `data/raw/bass_ii/original/`, with hashes in the [manifest](../data/manifests/bass_ii_acquisition_manifest.json). CSV rows include the header (B1 is row 2). Worksheet references preserve actual names, including `T'ien`.

FAQ page references use the file's saved Word pagination, not a new render: six `lastRenderedPageBreak` markers agree with seven pages in document properties. Exact paragraph IDs and complete text are in the [extraction](source_extracts/bass_ii_readme_extracted.md). Fresh rendering was unavailable because LibreOffice was not installed. The user-supplied filenames and expected portal aliases are recorded separately; hash agreement is with user-provided baselines, not an independently published NASA checksum.

## Matching method and result

**129 of 129 records matched uniquely** by exact `(CSV PI, CSV Test #) = (worksheet name, column C value)`. All 129 workbook test rows are used exactly once. No unmatched or duplicate join keys were found. Sample IDs agree after representing numeric Excel IDs as their literal decimal text; text suffixes/case are retained. This is source-record agreement, not evidence of independent physical replicates.

For comparisons only, Excel dates are decoded with their date format and compared to the CSV calendar date. Numeric cells are compared as decimal values; text and empty values are kept separate. The original Excel XML values and formats remain in the evidence JSON. No normalized comparison result replaces either original. All dates and numeric measurements agree, and all 19 CSV empty cells correspond to workbook empty cells. Sixteen literal `none` cells remain text in both sources.

## All records

Range A:P identifies the entire source record; C and D give exact test/sample cells. The Differences column names presentation differences, not measurement corrections. Date serialization and numeric Excel typing are expected representation differences for all rows and are documented separately.

| CSV Test # | CSV row | PI worksheet | XLSX record range | Test cell | Sample cell | Match status | Differences |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B1 | 2 | `Bhattacharjee` | A2:P2 | C2 | D2 | matched_exact | E2 case_comma_whitespace_presentation |
| B2 | 3 | `Bhattacharjee` | A3:P3 | C3 | D3 | matched_exact | E3 case_comma_whitespace_presentation |
| B3 | 4 | `Bhattacharjee` | A4:P4 | C4 | D4 | matched_exact | E4 comma_whitespace_presentation |
| B4 | 5 | `Bhattacharjee` | A5:P5 | C5 | D5 | matched_exact | E5 case_comma_whitespace_presentation |
| B5 | 6 | `Bhattacharjee` | A6:P6 | C6 | D6 | matched_exact | No text/content difference |
| B6 | 7 | `Bhattacharjee` | A7:P7 | C7 | D7 | matched_exact | E7 case_comma_whitespace_presentation; G7 comma_whitespace_presentation; H7 comma_whitespace_presentation |
| B7 | 8 | `Bhattacharjee` | A8:P8 | C8 | D8 | matched_exact | E8 comma_whitespace_presentation |
| B8 | 9 | `Bhattacharjee` | A9:P9 | C9 | D9 | matched_exact | E9 case_comma_whitespace_presentation; G9 comma_whitespace_presentation; H9 comma_whitespace_presentation |
| B9 | 10 | `Bhattacharjee` | A10:P10 | C10 | D10 | matched_exact | E10 case_comma_whitespace_presentation; G10 comma_whitespace_presentation; H10 comma_whitespace_presentation |
| B10 | 11 | `Bhattacharjee` | A11:P11 | C11 | D11 | matched_exact | E11 case_comma_whitespace_presentation; G11 comma_whitespace_presentation; H11 comma_whitespace_presentation |
| B11 | 12 | `Bhattacharjee` | A12:P12 | C12 | D12 | matched_exact | E12 case_comma_whitespace_presentation; G12 comma_whitespace_presentation; H12 comma_whitespace_presentation |
| B12 | 13 | `Bhattacharjee` | A13:P13 | C13 | D13 | matched_exact | E13 comma_whitespace_presentation |
| B13 | 14 | `Bhattacharjee` | A14:P14 | C14 | D14 | matched_exact | E14 comma_whitespace_presentation; G14 comma_whitespace_presentation; H14 comma_whitespace_presentation |
| B14 | 15 | `Bhattacharjee` | A15:P15 | C15 | D15 | matched_exact | E15 case_comma_whitespace_presentation; G15 comma_whitespace_presentation; H15 comma_whitespace_presentation |
| B15 | 16 | `Bhattacharjee` | A16:P16 | C16 | D16 | matched_exact | E16 case_comma_whitespace_presentation; H16 comma_whitespace_presentation |
| B16 | 17 | `Bhattacharjee` | A17:P17 | C17 | D17 | matched_exact | E17 case_comma_whitespace_presentation; H17 comma_whitespace_presentation |
| B17 | 18 | `Bhattacharjee` | A18:P18 | C18 | D18 | matched_exact | E18 case_comma_whitespace_presentation; G18 comma_whitespace_presentation; H18 comma_whitespace_presentation |
| B18 | 19 | `Bhattacharjee` | A19:P19 | C19 | D19 | matched_exact | E19 case_comma_whitespace_presentation; G19 comma_whitespace_presentation; H19 comma_whitespace_presentation |
| B19 | 20 | `Bhattacharjee` | A20:P20 | C20 | D20 | matched_exact | E20 case_comma_whitespace_presentation; G20 comma_whitespace_presentation; H20 comma_whitespace_presentation |
| B20 | 21 | `Bhattacharjee` | A21:P21 | C21 | D21 | matched_exact | E21 case_comma_whitespace_presentation; G21 comma_whitespace_presentation; H21 comma_whitespace_presentation |
| B21 | 22 | `Bhattacharjee` | A22:P22 | C22 | D22 | matched_exact | E22 case_comma_whitespace_presentation; G22 comma_whitespace_presentation |
| B22 | 23 | `Bhattacharjee` | A23:P23 | C23 | D23 | matched_exact | E23 case_comma_whitespace_presentation; G23 comma_whitespace_presentation; H23 comma_whitespace_presentation |
| F1 | 24 | `Ferkul` | A2:P2 | C2 | D2 | matched_exact | No text/content difference |
| F2 | 25 | `Ferkul` | A3:P3 | C3 | D3 | matched_exact | No text/content difference |
| F3 | 26 | `Ferkul` | A4:P4 | C4 | D4 | matched_exact | No text/content difference |
| F4 | 27 | `Ferkul` | A5:P5 | C5 | D5 | matched_exact | No text/content difference |
| M1 | 28 | `Miller` | A2:P2 | C2 | D2 | matched_exact | E2 case_comma_whitespace_presentation; G2 comma_whitespace_presentation; H2 comma_whitespace_presentation |
| M2 | 29 | `Miller` | A3:P3 | C3 | D3 | matched_exact | E3 case_comma_whitespace_presentation; G3 comma_whitespace_presentation; H3 comma_whitespace_presentation |
| M3 | 30 | `Miller` | A4:P4 | C4 | D4 | matched_exact | E4 case_comma_whitespace_presentation; G4 comma_whitespace_presentation; H4 comma_whitespace_presentation |
| M4 | 31 | `Miller` | A5:P5 | C5 | D5 | matched_exact | E5 case_comma_whitespace_presentation; G5 comma_whitespace_presentation; H5 comma_whitespace_presentation |
| M5 | 32 | `Miller` | A6:P6 | C6 | D6 | matched_exact | E6 case_comma_whitespace_presentation; H6 comma_whitespace_presentation |
| M6 | 33 | `Miller` | A7:P7 | C7 | D7 | matched_exact | E7 case_comma_whitespace_presentation; G7 comma_whitespace_presentation; H7 comma_whitespace_presentation |
| M7 | 34 | `Miller` | A8:P8 | C8 | D8 | matched_exact | E8 case_comma_whitespace_presentation; G8 comma_whitespace_presentation; H8 comma_whitespace_presentation |
| M8 | 35 | `Miller` | A9:P9 | C9 | D9 | matched_exact | E9 case_comma_whitespace_presentation; G9 comma_whitespace_presentation; H9 comma_whitespace_presentation |
| M9 | 36 | `Miller` | A10:P10 | C10 | D10 | matched_exact | E10 case_comma_whitespace_presentation; G10 comma_whitespace_presentation; H10 comma_whitespace_presentation; I10 comma_whitespace_presentation |
| M10 | 37 | `Miller` | A11:P11 | C11 | D11 | matched_exact | E11 case_comma_whitespace_presentation; G11 comma_whitespace_presentation; H11 comma_whitespace_presentation; I11 comma_whitespace_presentation |
| M11 | 38 | `Miller` | A12:P12 | C12 | D12 | matched_exact | E12 case_comma_whitespace_presentation; G12 comma_whitespace_presentation; H12 comma_whitespace_presentation |
| M12 | 39 | `Miller` | A13:P13 | C13 | D13 | matched_exact | E13 case_comma_whitespace_presentation; G13 comma_whitespace_presentation |
| M13 | 40 | `Miller` | A14:P14 | C14 | D14 | matched_exact | E14 case_comma_whitespace_presentation; G14 comma_whitespace_presentation; H14 comma_whitespace_presentation |
| M14 | 41 | `Miller` | A15:P15 | C15 | D15 | matched_exact | E15 case_comma_whitespace_presentation; G15 comma_whitespace_presentation; H15 comma_whitespace_presentation |
| M15 | 42 | `Miller` | A16:P16 | C16 | D16 | matched_exact | E16 case_comma_whitespace_presentation; G16 comma_whitespace_presentation; H16 comma_whitespace_presentation; I16 comma_whitespace_presentation |
| M16 | 43 | `Miller` | A17:P17 | C17 | D17 | matched_exact | E17 case_comma_whitespace_presentation; G17 comma_whitespace_presentation; H17 comma_whitespace_presentation; I17 comma_whitespace_presentation |
| M17 | 44 | `Miller` | A18:P18 | C18 | D18 | matched_exact | E18 case_comma_whitespace_presentation; G18 comma_whitespace_presentation; H18 comma_whitespace_presentation |
| M18 | 45 | `Miller` | A19:P19 | C19 | D19 | matched_exact | E19 case_comma_whitespace_presentation; G19 comma_whitespace_presentation; H19 comma_whitespace_presentation |
| M19 | 46 | `Miller` | A20:P20 | C20 | D20 | matched_exact | E20 case_comma_whitespace_presentation; G20 comma_whitespace_presentation; H20 comma_whitespace_presentation; I20 comma_whitespace_presentation |
| M20 | 47 | `Miller` | A21:P21 | C21 | D21 | matched_exact | E21 case_comma_whitespace_presentation; G21 comma_whitespace_presentation; H21 comma_whitespace_presentation |
| O1 | 48 | `Olson` | A2:P2 | C2 | D2 | matched_exact | G2 comma_whitespace_presentation; H2 comma_whitespace_presentation |
| O2 | 49 | `Olson` | A3:P3 | C3 | D3 | matched_exact | G3 comma_whitespace_presentation |
| O3a | 50 | `Olson` | A4:P4 | C4 | D4 | matched_exact | H4 comma_whitespace_presentation |
| O3b | 51 | `Olson` | A5:P5 | C5 | D5 | matched_exact | H5 comma_whitespace_presentation; I5 comma_whitespace_presentation |
| O4 | 52 | `Olson` | A6:P6 | C6 | D6 | matched_exact | G6 comma_whitespace_presentation; H6 comma_whitespace_presentation |
| O5a | 53 | `Olson` | A7:P7 | C7 | D7 | matched_exact | E7 case_comma_whitespace_presentation; G7 comma_whitespace_presentation; H7 comma_whitespace_presentation |
| O5b | 54 | `Olson` | A8:P8 | C8 | D8 | matched_exact | E8 case_comma_whitespace_presentation; H8 comma_whitespace_presentation |
| O6 | 55 | `Olson` | A9:P9 | C9 | D9 | matched_exact | G9 comma_whitespace_presentation |
| O7 | 56 | `Olson` | A10:P10 | C10 | D10 | matched_exact | G10 comma_whitespace_presentation |
| O8a | 57 | `Olson` | A11:P11 | C11 | D11 | matched_exact | G11 comma_whitespace_presentation |
| O8b | 58 | `Olson` | A12:P12 | C12 | D12 | matched_exact | G12 comma_whitespace_presentation |
| O9 | 59 | `Olson` | A13:P13 | C13 | D13 | matched_exact | G13 comma_whitespace_presentation |
| O10 | 60 | `Olson` | A14:P14 | C14 | D14 | matched_exact | G14 comma_whitespace_presentation; H14 comma_whitespace_presentation |
| O11 | 61 | `Olson` | A15:P15 | C15 | D15 | matched_exact | G15 comma_whitespace_presentation; H15 comma_whitespace_presentation |
| O12 | 62 | `Olson` | A16:P16 | C16 | D16 | matched_exact | G16 comma_whitespace_presentation |
| O13a | 63 | `Olson` | A17:P17 | C17 | D17 | matched_exact | E17 case_comma_whitespace_presentation; G17 comma_whitespace_presentation; H17 comma_whitespace_presentation |
| O13b | 64 | `Olson` | A18:P18 | C18 | D18 | matched_exact | E18 case_comma_whitespace_presentation; G18 comma_whitespace_presentation; H18 comma_whitespace_presentation |
| O14 | 65 | `Olson` | A19:P19 | C19 | D19 | matched_exact | G19 comma_whitespace_presentation |
| O15a | 66 | `Olson` | A20:P20 | C20 | D20 | matched_exact | G20 comma_whitespace_presentation; H20 comma_whitespace_presentation |
| O15b | 67 | `Olson` | A21:P21 | C21 | D21 | matched_exact | G21 comma_whitespace_presentation; H21 comma_whitespace_presentation |
| O16 | 68 | `Olson` | A22:P22 | C22 | D22 | matched_exact | No text/content difference |
| O17 | 69 | `Olson` | A23:P23 | C23 | D23 | matched_exact | G23 comma_whitespace_presentation; H23 comma_whitespace_presentation |
| O18 | 70 | `Olson` | A24:P24 | C24 | D24 | matched_exact | G24 comma_whitespace_presentation; H24 comma_whitespace_presentation |
| O19 | 71 | `Olson` | A25:P25 | C25 | D25 | matched_exact | G25 comma_whitespace_presentation |
| O20 | 72 | `Olson` | A26:P26 | C26 | D26 | matched_exact | G26 comma_whitespace_presentation; H26 comma_whitespace_presentation |
| O21 | 73 | `Olson` | A27:P27 | C27 | D27 | matched_exact | G27 comma_whitespace_presentation |
| O22 | 74 | `Olson` | A28:P28 | C28 | D28 | matched_exact | G28 comma_whitespace_presentation |
| P1 | 75 | `Fernandez-Pello` | A2:P2 | C2 | D2 | matched_exact | H2 comma_whitespace_presentation |
| P2 | 76 | `Fernandez-Pello` | A3:P3 | C3 | D3 | matched_exact | H3 comma_whitespace_presentation |
| P3a | 77 | `Fernandez-Pello` | A4:P4 | C4 | D4 | matched_exact | H4 comma_whitespace_presentation |
| P3b | 78 | `Fernandez-Pello` | A5:P5 | C5 | D5 | matched_exact | H5 comma_whitespace_presentation |
| P4 | 79 | `Fernandez-Pello` | A6:P6 | C6 | D6 | matched_exact | G6 comma_whitespace_presentation; H6 comma_whitespace_presentation |
| P5 | 80 | `Fernandez-Pello` | A7:P7 | C7 | D7 | matched_exact | G7 comma_whitespace_presentation |
| P6 | 81 | `Fernandez-Pello` | A8:P8 | C8 | D8 | matched_exact | G8 comma_whitespace_presentation; H8 comma_whitespace_presentation |
| P8 | 82 | `Fernandez-Pello` | A9:P9 | C9 | D9 | matched_exact | G9 comma_whitespace_presentation; H9 comma_whitespace_presentation |
| P9 | 83 | `Fernandez-Pello` | A10:P10 | C10 | D10 | matched_exact | G10 comma_whitespace_presentation |
| P10 | 84 | `Fernandez-Pello` | A11:P11 | C11 | D11 | matched_exact | G11 comma_whitespace_presentation; H11 comma_whitespace_presentation |
| P12 | 85 | `Fernandez-Pello` | A12:P12 | C12 | D12 | matched_exact | G12 comma_whitespace_presentation; H12 comma_whitespace_presentation |
| P13a | 86 | `Fernandez-Pello` | A13:P13 | C13 | D13 | matched_exact | G13 comma_whitespace_presentation |
| P13b | 87 | `Fernandez-Pello` | A14:P14 | C14 | D14 | matched_exact | G14 comma_whitespace_presentation |
| P14 | 88 | `Fernandez-Pello` | A15:P15 | C15 | D15 | matched_exact | G15 comma_whitespace_presentation; H15 comma_whitespace_presentation |
| P15 | 89 | `Fernandez-Pello` | A16:P16 | C16 | D16 | matched_exact | G16 comma_whitespace_presentation; H16 comma_whitespace_presentation; I16 comma_whitespace_presentation |
| P16 | 90 | `Fernandez-Pello` | A17:P17 | C17 | D17 | matched_exact | G17 comma_whitespace_presentation; H17 comma_whitespace_presentation; I17 comma_whitespace_presentation |
| P17 | 91 | `Fernandez-Pello` | A18:P18 | C18 | D18 | matched_exact | G18 comma_whitespace_presentation; H18 comma_whitespace_presentation |
| P18 | 92 | `Fernandez-Pello` | A19:P19 | C19 | D19 | matched_exact | G19 comma_whitespace_presentation; H19 comma_whitespace_presentation |
| P19 | 93 | `Fernandez-Pello` | A20:P20 | C20 | D20 | matched_exact | G20 comma_whitespace_presentation; H20 comma_whitespace_presentation; I20 comma_whitespace_presentation |
| P20 | 94 | `Fernandez-Pello` | A21:P21 | C21 | D21 | matched_exact | G21 comma_whitespace_presentation; H21 comma_whitespace_presentation |
| P21a | 95 | `Fernandez-Pello` | A22:P22 | C22 | D22 | matched_exact | No text/content difference |
| P21b | 96 | `Fernandez-Pello` | A23:P23 | C23 | D23 | matched_exact | No text/content difference |
| P22a | 97 | `Fernandez-Pello` | A24:P24 | C24 | D24 | matched_exact | G24 comma_whitespace_presentation; H24 comma_whitespace_presentation |
| P22b | 98 | `Fernandez-Pello` | A25:P25 | C25 | D25 | matched_exact | G25 comma_whitespace_presentation |
| P23 | 99 | `Fernandez-Pello` | A26:P26 | C26 | D26 | matched_exact | G26 comma_whitespace_presentation; H26 comma_whitespace_presentation |
| P24 | 100 | `Fernandez-Pello` | A27:P27 | C27 | D27 | matched_exact | G27 comma_whitespace_presentation; H27 comma_whitespace_presentation |
| P25 | 101 | `Fernandez-Pello` | A28:P28 | C28 | D28 | matched_exact | G28 comma_whitespace_presentation |
| T1 | 102 | `T'ien` | A2:P2 | C2 | D2 | matched_exact | E2 word_order_only_reviewed |
| T2 | 103 | `T'ien` | A3:P3 | C3 | D3 | matched_exact | E3 word_order_only_reviewed; G3 comma_whitespace_presentation; H3 comma_whitespace_presentation |
| T3 | 104 | `T'ien` | A4:P4 | C4 | D4 | matched_exact | No text/content difference |
| T4 | 105 | `T'ien` | A5:P5 | C5 | D5 | matched_exact | E5 word_order_only_reviewed; G5 comma_whitespace_presentation; H5 comma_whitespace_presentation |
| T5 | 106 | `T'ien` | A6:P6 | C6 | D6 | matched_exact | G6 comma_whitespace_presentation; H6 comma_whitespace_presentation |
| T6 | 107 | `T'ien` | A7:P7 | C7 | D7 | matched_exact | H7 comma_whitespace_presentation |
| T7 | 108 | `T'ien` | A8:P8 | C8 | D8 | matched_exact | G8 comma_whitespace_presentation; H8 comma_whitespace_presentation |
| T9 | 109 | `T'ien` | A9:P9 | C9 | D9 | matched_exact | No text/content difference |
| T10 | 110 | `T'ien` | A10:P10 | C10 | D10 | matched_exact | No text/content difference |
| T11 | 111 | `T'ien` | A11:P11 | C11 | D11 | matched_exact | No text/content difference |
| T12 | 112 | `T'ien` | A12:P12 | C12 | D12 | matched_exact | No text/content difference |
| T13 | 113 | `T'ien` | A13:P13 | C13 | D13 | matched_exact | H13 comma_whitespace_presentation |
| T14 | 114 | `T'ien` | A14:P14 | C14 | D14 | matched_exact | H14 comma_whitespace_presentation |
| T15 | 115 | `T'ien` | A15:P15 | C15 | D15 | matched_exact | E15 word_order_only_reviewed; H15 comma_whitespace_presentation |
| T16 | 116 | `T'ien` | A16:P16 | C16 | D16 | matched_exact | H16 comma_whitespace_presentation |
| T17 | 117 | `T'ien` | A17:P17 | C17 | D17 | matched_exact | H17 comma_whitespace_presentation |
| T18 | 118 | `T'ien` | A18:P18 | C18 | D18 | matched_exact | H18 comma_whitespace_presentation |
| T19 | 119 | `T'ien` | A19:P19 | C19 | D19 | matched_exact | G19 comma_whitespace_presentation |
| T20 | 120 | `T'ien` | A20:P20 | C20 | D20 | matched_exact | G20 comma_whitespace_presentation; H20 comma_whitespace_presentation |
| T21 | 121 | `T'ien` | A21:P21 | C21 | D21 | matched_exact | G21 comma_whitespace_presentation; H21 comma_whitespace_presentation |
| T22 | 122 | `T'ien` | A22:P22 | C22 | D22 | matched_exact | G22 comma_whitespace_presentation; H22 comma_whitespace_presentation |
| T23 | 123 | `T'ien` | A23:P23 | C23 | D23 | matched_exact | E23 comma_whitespace_presentation; G23 comma_whitespace_presentation |
| T24 | 124 | `T'ien` | A24:P24 | C24 | D24 | matched_exact | E24 comma_whitespace_presentation |
| T25 | 125 | `T'ien` | A25:P25 | C25 | D25 | matched_exact | E25 word_order_only_reviewed; G25 comma_whitespace_presentation; H25 comma_whitespace_presentation |
| T26 | 126 | `T'ien` | A26:P26 | C26 | D26 | matched_exact | E26 word_order_only_reviewed; G26 comma_whitespace_presentation; H26 comma_whitespace_presentation |
| T27 | 127 | `T'ien` | A27:P27 | C27 | D27 | matched_exact | G27 comma_whitespace_presentation; H27 comma_whitespace_presentation |
| T28a | 128 | `T'ien` | A28:P28 | C28 | D28 | matched_exact | No text/content difference |
| T28b | 129 | `T'ien` | A29:P29 | C29 | D29 | matched_exact | No text/content difference |
| T29 | 130 | `T'ien` | A30:P30 | C30 | D30 | matched_exact | G30 comma_whitespace_presentation; H30 comma_whitespace_presentation |

## Presentation-sensitive comparison summary

| CSV field | Comparison counts |
| --- | --- |
| `Fuel Sample Material` | case_comma_whitespace_presentation: 41; comma_whitespace_presentation: 6; exact_text: 76; word_order_only_reviewed: 6 |
| `Fan display` | numeric_equivalent: 19; comma_whitespace_presentation: 89; exact_text: 8; both_empty: 13 |
| `Air display` | numeric_equivalent: 25; comma_whitespace_presentation: 85; exact_text: 15; both_empty: 4 |
| `Radiometer gain   (1000   250   50   10)` | numeric_equivalent: 110; exact_text: 10; comma_whitespace_presentation: 9 |

There are **236 text presentation differences** in these four fields: 189 comma/whitespace differences, 41 case plus comma/whitespace differences, and 6 word-order differences. No whitespace-only mismatch or additional content disagreement was found. Comma/space comparison is a diagnostic presentation rule, not permission to interpret a setting sequence or change punctuation in the stored data. The six explicitly reviewed material pairs are CSV `2 cm SIBAL` versus workbook `SIBAL 2 cm`, in T1, T2, T4, T15, T25 and T26. No missing-value disagreement was found. No physical interchangeability is inferred from text agreement.

## Both original representations for all four fields

JSON notation preserves repeated spaces and empty strings. Workbook numeric values are numbers, empty cells are null, and text values have quotes. Original number formats and XML lexemes remain in the evidence JSON. No values below were written back to the parser outputs.

| Test | CSV row | CSV field | CSV raw string | Workbook sheet!cell | Workbook decoded original | Comparison |
| --- | --- | --- | --- | --- | --- | --- |
| B1 | 2 | `Fuel Sample Material` | `"100 micron PMMA film   2 cm wide"` | `Bhattacharjee!E2` | `"100 micron pmma film, 2 cm wide"` | case_comma_whitespace_presentation |
| B1 | 2 | `Fan display` | `"62"` | `Bhattacharjee!G2` | `62` | numeric_equivalent |
| B1 | 2 | `Air display` | `"5"` | `Bhattacharjee!H2` | `5` | numeric_equivalent |
| B1 | 2 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Bhattacharjee!I2` | `50` | numeric_equivalent |
| B2 | 3 | `Fuel Sample Material` | `"200 micron PMMA film   2 cm wide"` | `Bhattacharjee!E3` | `"200 micron pmma film, 2 cm wide"` | case_comma_whitespace_presentation |
| B2 | 3 | `Fan display` | `"62"` | `Bhattacharjee!G3` | `62` | numeric_equivalent |
| B2 | 3 | `Air display` | `"5"` | `Bhattacharjee!H3` | `5` | numeric_equivalent |
| B2 | 3 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Bhattacharjee!I3` | `50` | numeric_equivalent |
| B3 | 4 | `Fuel Sample Material` | `"100 micron film   2 cm wide"` | `Bhattacharjee!E4` | `"100 micron film, 2 cm wide"` | comma_whitespace_presentation |
| B3 | 4 | `Fan display` | `"47"` | `Bhattacharjee!G4` | `47` | numeric_equivalent |
| B3 | 4 | `Air display` | `"2"` | `Bhattacharjee!H4` | `2` | numeric_equivalent |
| B3 | 4 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Bhattacharjee!I4` | `50` | numeric_equivalent |
| B4 | 5 | `Fuel Sample Material` | `"300 micron PMMA film   2 cm wide "` | `Bhattacharjee!E5` | `"300 micron pmma film, 2 cm wide "` | case_comma_whitespace_presentation |
| B4 | 5 | `Fan display` | `"61"` | `Bhattacharjee!G5` | `61` | numeric_equivalent |
| B4 | 5 | `Air display` | `"5"` | `Bhattacharjee!H5` | `5` | numeric_equivalent |
| B4 | 5 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Bhattacharjee!I5` | `50` | numeric_equivalent |
| B5 | 6 | `Fuel Sample Material` | `"200 micron  2 cm wide "` | `Bhattacharjee!E6` | `"200 micron  2 cm wide "` | exact_text |
| B5 | 6 | `Fan display` | `"59"` | `Bhattacharjee!G6` | `59` | numeric_equivalent |
| B5 | 6 | `Air display` | `"5"` | `Bhattacharjee!H6` | `5` | numeric_equivalent |
| B5 | 6 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Bhattacharjee!I6` | `50` | numeric_equivalent |
| B6 | 7 | `Fuel Sample Material` | `"2 cm 0.1 mm PMMA film"` | `Bhattacharjee!E7` | `"2 cm 0.1 mm pmma film"` | case_comma_whitespace_presentation |
| B6 | 7 | `Fan display` | `"0.9   1.3   2.75"` | `Bhattacharjee!G7` | `"0.9, 1.3, 2.75"` | comma_whitespace_presentation |
| B6 | 7 | `Air display` | `"3   5   approaching 10"` | `Bhattacharjee!H7` | `"3, 5, approaching 10"` | comma_whitespace_presentation |
| B6 | 7 | `Radiometer gain   (1000   250   50   10)` | `"10"` | `Bhattacharjee!I7` | `10` | numeric_equivalent |
| B7 | 8 | `Fuel Sample Material` | `"400 micron film   2 cm wide"` | `Bhattacharjee!E8` | `"400 micron film, 2 cm wide"` | comma_whitespace_presentation |
| B7 | 8 | `Fan display` | `"47"` | `Bhattacharjee!G8` | `47` | numeric_equivalent |
| B7 | 8 | `Air display` | `"2"` | `Bhattacharjee!H8` | `2` | numeric_equivalent |
| B7 | 8 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Bhattacharjee!I8` | `50` | numeric_equivalent |
| B8 | 9 | `Fuel Sample Material` | `"2 cm   0.2 mm PMMA film"` | `Bhattacharjee!E9` | `"2 cm, 0.2 mm pmma film"` | case_comma_whitespace_presentation |
| B8 | 9 | `Fan display` | `"1.4    incr to 10.0"` | `Bhattacharjee!G9` | `"1.4 , incr to 10.0"` | comma_whitespace_presentation |
| B8 | 9 | `Air display` | `"10   max"` | `Bhattacharjee!H9` | `"10, max"` | comma_whitespace_presentation |
| B8 | 9 | `Radiometer gain   (1000   250   50   10)` | `"10"` | `Bhattacharjee!I9` | `10` | numeric_equivalent |
| B9 | 10 | `Fuel Sample Material` | `"2 cm   0.1 mm PMMA film"` | `Bhattacharjee!E10` | `"2 cm, 0.1 mm pmma film"` | case_comma_whitespace_presentation |
| B9 | 10 | `Fan display` | `"0.6   0.35"` | `Bhattacharjee!G10` | `"0.6, 0.35"` | comma_whitespace_presentation |
| B9 | 10 | `Air display` | `"2   <1"` | `Bhattacharjee!H10` | `"2, <1"` | comma_whitespace_presentation |
| B9 | 10 | `Radiometer gain   (1000   250   50   10)` | `"10"` | `Bhattacharjee!I10` | `10` | numeric_equivalent |
| B10 | 11 | `Fuel Sample Material` | `"1 cm   0.2 mm PMMA film"` | `Bhattacharjee!E11` | `"1 cm, 0.2 mm pmma film"` | case_comma_whitespace_presentation |
| B10 | 11 | `Fan display` | `"1.7 (52)   1.25   0.9   0.6   0.4   0.35"` | `Bhattacharjee!G11` | `"1.7 (52), 1.25, 0.9, 0.6, 0.4, 0.35"` | comma_whitespace_presentation |
| B10 | 11 | `Air display` | `"5  4  3  2  1"` | `Bhattacharjee!H11` | `"5,4,3,2,1"` | comma_whitespace_presentation |
| B10 | 11 | `Radiometer gain   (1000   250   50   10)` | `"10"` | `Bhattacharjee!I11` | `10` | numeric_equivalent |
| B11 | 12 | `Fuel Sample Material` | `"2 cm   0.2 mm PMMA film"` | `Bhattacharjee!E12` | `"2 cm, 0.2 mm pmma film"` | case_comma_whitespace_presentation |
| B11 | 12 | `Fan display` | `"2.5 (59)   1.3   0.7   0.5   0.35"` | `Bhattacharjee!G12` | `"2.5 (59), 1.3, 0.7, 0.5, 0.35"` | comma_whitespace_presentation |
| B11 | 12 | `Air display` | `"5   3   1   <1"` | `Bhattacharjee!H12` | `"5, 3, 1, <1"` | comma_whitespace_presentation |
| B11 | 12 | `Radiometer gain   (1000   250   50   10)` | `"10"` | `Bhattacharjee!I12` | `10` | numeric_equivalent |
| B12 | 13 | `Fuel Sample Material` | `"300 micron film   2 cm wide"` | `Bhattacharjee!E13` | `"300 micron film, 2 cm wide"` | comma_whitespace_presentation |
| B12 | 13 | `Fan display` | `"46.5"` | `Bhattacharjee!G13` | `46.5` | numeric_equivalent |
| B12 | 13 | `Air display` | `"2"` | `Bhattacharjee!H13` | `2` | numeric_equivalent |
| B12 | 13 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Bhattacharjee!I13` | `50` | numeric_equivalent |
| B13 | 14 | `Fuel Sample Material` | `"2 cm   0.4 mm thick film"` | `Bhattacharjee!E14` | `"2 cm, 0.4 mm thick film"` | comma_whitespace_presentation |
| B13 | 14 | `Fan display` | `"3.5 (68)    1.7   1.25   0.9   0.6   0.4   0.35"` | `Bhattacharjee!G14` | `"3.5 (68),  1.7, 1.25, 0.9, 0.6, 0.4, 0.35"` | comma_whitespace_presentation |
| B13 | 14 | `Air display` | `"10   5  4  3  2  1"` | `Bhattacharjee!H14` | `"10, 5,4,3,2,1"` | comma_whitespace_presentation |
| B13 | 14 | `Radiometer gain   (1000   250   50   10)` | `"10"` | `Bhattacharjee!I14` | `10` | numeric_equivalent |
| B14 | 15 | `Fuel Sample Material` | `"1 cm wide 200 micron thick PMMA"` | `Bhattacharjee!E15` | `"1 cm wide 200 micron thick pmma"` | case_comma_whitespace_presentation |
| B14 | 15 | `Fan display` | `"pot 0.9   0.5 and down"` | `Bhattacharjee!G15` | `"pot 0.9, 0.5 and down"` | comma_whitespace_presentation |
| B14 | 15 | `Air display` | `"5  3  2   ext"` | `Bhattacharjee!H15` | `"5,3,2, ext"` | comma_whitespace_presentation |
| B14 | 15 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Bhattacharjee!I15` | `250` | numeric_equivalent |
| B15 | 16 | `Fuel Sample Material` | `"2 cm   0.1 mm PMMA film"` | `Bhattacharjee!E16` | `"2 cm, 0.1 mm pmma film"` | case_comma_whitespace_presentation |
| B15 | 16 | `Fan display` | `"1.4 (50) incr to 10.0 pot"` | `Bhattacharjee!G16` | `"1.4 (50) incr to 10.0 pot"` | exact_text |
| B15 | 16 | `Air display` | `"10   max"` | `Bhattacharjee!H16` | `"10, max"` | comma_whitespace_presentation |
| B15 | 16 | `Radiometer gain   (1000   250   50   10)` | `"10"` | `Bhattacharjee!I16` | `10` | numeric_equivalent |
| B16 | 17 | `Fuel Sample Material` | `"2 cm 100 micron thick PMMA"` | `Bhattacharjee!E17` | `"2 cm 100 micron thick pmma"` | case_comma_whitespace_presentation |
| B16 | 17 | `Fan display` | `"44 (pot 0.68)"` | `Bhattacharjee!G17` | `"44 (pot 0.68)"` | exact_text |
| B16 | 17 | `Air display` | `"3  0.5 pot   0.4 pot"` | `Bhattacharjee!H17` | `"3,0.5 pot, 0.4 pot"` | comma_whitespace_presentation |
| B16 | 17 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Bhattacharjee!I17` | `250` | numeric_equivalent |
| B17 | 18 | `Fuel Sample Material` | `"1 cm wide 200 micron thick PMMA"` | `Bhattacharjee!E18` | `"1 cm wide 200 micron thick pmma"` | case_comma_whitespace_presentation |
| B17 | 18 | `Fan display` | `"pot 1.2 (48)    0.9   0.4 "` | `Bhattacharjee!G18` | `"pot 1.2 (48),  0.9, 0.4 "` | comma_whitespace_presentation |
| B17 | 18 | `Air display` | `"5   3    pot 0.4"` | `Bhattacharjee!H18` | `"5, 3,  pot 0.4"` | comma_whitespace_presentation |
| B17 | 18 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Bhattacharjee!I18` | `250` | numeric_equivalent |
| B18 | 19 | `Fuel Sample Material` | `"1 cm wide 200 micron thick PMMA"` | `Bhattacharjee!E19` | `"1 cm wide 200 micron thick pmma"` | case_comma_whitespace_presentation |
| B18 | 19 | `Fan display` | `"pot 1.02 (47)   incr to 7.0"` | `Bhattacharjee!G19` | `"pot 1.02 (47), incr to 7.0"` | comma_whitespace_presentation |
| B18 | 19 | `Air display` | `"10   blowoff"` | `Bhattacharjee!H19` | `"10, blowoff"` | comma_whitespace_presentation |
| B18 | 19 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Bhattacharjee!I19` | `250` | numeric_equivalent |
| B19 | 20 | `Fuel Sample Material` | `"2 cm 100 micron thick PMMA"` | `Bhattacharjee!E20` | `"2 cm 100 micron thick pmma"` | case_comma_whitespace_presentation |
| B19 | 20 | `Fan display` | `"47 (pot 1.05)   incr to pot 6.0"` | `Bhattacharjee!G20` | `"47 (pot 1.05), incr to pot 6.0"` | comma_whitespace_presentation |
| B19 | 20 | `Air display` | `"10   blowoff"` | `Bhattacharjee!H20` | `"10, blowoff"` | comma_whitespace_presentation |
| B19 | 20 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Bhattacharjee!I20` | `250` | numeric_equivalent |
| B20 | 21 | `Fuel Sample Material` | `"2 cm 100 micron thick PMMA"` | `Bhattacharjee!E21` | `"2 cm 100 micron thick pmma"` | case_comma_whitespace_presentation |
| B20 | 21 | `Fan display` | `"48   pot 0.9   0.5"` | `Bhattacharjee!G21` | `"48, pot 0.9, 0.5"` | comma_whitespace_presentation |
| B20 | 21 | `Air display` | `"5   3      pot 0.5"` | `Bhattacharjee!H21` | `"5, 3, , pot 0.5"` | comma_whitespace_presentation |
| B20 | 21 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Bhattacharjee!I21` | `250` | numeric_equivalent |
| B21 | 22 | `Fuel Sample Material` | `"1 cm wide 200 micron thick PMMA"` | `Bhattacharjee!E22` | `"1 cm wide 200 micron thick pmma"` | case_comma_whitespace_presentation |
| B21 | 22 | `Fan display` | `"53   and down"` | `Bhattacharjee!G22` | `"53, and down"` | comma_whitespace_presentation |
| B21 | 22 | `Air display` | `"5 down to ext"` | `Bhattacharjee!H22` | `"5 down to ext"` | exact_text |
| B21 | 22 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Bhattacharjee!I22` | `250` | numeric_equivalent |
| B22 | 23 | `Fuel Sample Material` | `"1 cm wide 200 micron thick PMMA"` | `Bhattacharjee!E23` | `"1 cm wide 200 micron thick pmma"` | case_comma_whitespace_presentation |
| B22 | 23 | `Fan display` | `"53   42   41   40.5"` | `Bhattacharjee!G23` | `"53, 42, 41, 40.5"` | comma_whitespace_presentation |
| B22 | 23 | `Air display` | `"5   2   0"` | `Bhattacharjee!H23` | `"5, 2, 0"` | comma_whitespace_presentation |
| B22 | 23 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Bhattacharjee!I23` | `250` | numeric_equivalent |
| F1 | 24 | `Fuel Sample Material` | `"Nomex natural (nomex III)"` | `Ferkul!E2` | `"Nomex natural (nomex III)"` | exact_text |
| F1 | 24 | `Fan display` | `"82"` | `Ferkul!G2` | `82` | numeric_equivalent |
| F1 | 24 | `Air display` | `"9.5"` | `Ferkul!H2` | `9.5` | numeric_equivalent |
| F1 | 24 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Ferkul!I2` | `250` | numeric_equivalent |
| F2 | 25 | `Fuel Sample Material` | `"Nomex natural (nomex III)"` | `Ferkul!E3` | `"Nomex natural (nomex III)"` | exact_text |
| F2 | 25 | `Fan display` | `"92"` | `Ferkul!G3` | `92` | numeric_equivalent |
| F2 | 25 | `Air display` | `"15"` | `Ferkul!H3` | `15` | numeric_equivalent |
| F2 | 25 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Ferkul!I3` | `250` | numeric_equivalent |
| F3 | 26 | `Fuel Sample Material` | `"Nomex natural (nomex III)"` | `Ferkul!E4` | `"Nomex natural (nomex III)"` | exact_text |
| F3 | 26 | `Fan display` | `"61"` | `Ferkul!G4` | `61` | numeric_equivalent |
| F3 | 26 | `Air display` | `"8"` | `Ferkul!H4` | `8` | numeric_equivalent |
| F3 | 26 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Ferkul!I4` | `50` | numeric_equivalent |
| F4 | 27 | `Fuel Sample Material` | `"Japan Wax candle"` | `Ferkul!E5` | `"Japan Wax candle"` | exact_text |
| F4 | 27 | `Fan display` | `"see notes"` | `Ferkul!G5` | `"see notes"` | exact_text |
| F4 | 27 | `Air display` | `"3 ign"` | `Ferkul!H5` | `"3 ign"` | exact_text |
| F4 | 27 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Ferkul!I5` | `250` | numeric_equivalent |
| M1 | 28 | `Fuel Sample Material` | `"1 mm thick PMMA   1 sided   2 cm"` | `Miller!E2` | `"1 mm thick pmma, 1 sided, 2 cm"` | case_comma_whitespace_presentation |
| M1 | 28 | `Fan display` | `"58   54"` | `Miller!G2` | `"58, 54"` | comma_whitespace_presentation |
| M1 | 28 | `Air display` | `"10  8"` | `Miller!H2` | `"10,8"` | comma_whitespace_presentation |
| M1 | 28 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Miller!I2` | `50` | numeric_equivalent |
| M2 | 29 | `Fuel Sample Material` | `"3 mm thick PMMA 1 sided    2 cm wide"` | `Miller!E3` | `"3 mm thick pmma 1 sided , 2 cm wide"` | case_comma_whitespace_presentation |
| M2 | 29 | `Fan display` | `"116 (pot 9.3)    89   80   84"` | `Miller!G3` | `"116 (pot 9.3),  89, 80, 84"` | comma_whitespace_presentation |
| M2 | 29 | `Air display` | `"20  15  13   14"` | `Miller!H3` | `"20,15,13, 14"` | comma_whitespace_presentation |
| M2 | 29 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Miller!I3` | `50` | numeric_equivalent |
| M3 | 30 | `Fuel Sample Material` | `"2 cm wide   5 mm thick 1 sided PMMA"` | `Miller!E4` | `"2 cm wide, 5 mm thick 1 sided pmma"` | case_comma_whitespace_presentation |
| M3 | 30 | `Fan display` | `"3.0  3.1  3.2  6.4  5.5  5.4"` | `Miller!G4` | `"3.0,3.1,3.2,6.4,5.5,5.4"` | comma_whitespace_presentation |
| M3 | 30 | `Air display` | `"10   20  18"` | `Miller!H4` | `"10, 20,18"` | comma_whitespace_presentation |
| M3 | 30 | `Radiometer gain   (1000   250   50   10)` | `"250>50>250"` | `Miller!I4` | `"250>50>250"` | exact_text |
| M4 | 31 | `Fuel Sample Material` | `"5 mm thick PMMA   2 cm wide"` | `Miller!E5` | `"5 mm thick pmma, 2 cm wide"` | case_comma_whitespace_presentation |
| M4 | 31 | `Fan display` | `"52   47   43"` | `Miller!G5` | `"52, 47, 43"` | comma_whitespace_presentation |
| M4 | 31 | `Air display` | `"5   4   3"` | `Miller!H5` | `"5, 4, 3"` | comma_whitespace_presentation |
| M4 | 31 | `Radiometer gain   (1000   250   50   10)` | `"250>50"` | `Miller!I5` | `"250>50"` | exact_text |
| M5 | 32 | `Fuel Sample Material` | `"3 mm thick PMMA   2 sided   2 cm thick"` | `Miller!E6` | `"3 mm thick pmma, 2 sided, 2 cm thick"` | case_comma_whitespace_presentation |
| M5 | 32 | `Fan display` | `""` | `Miller!G6` | `null` | both_empty |
| M5 | 32 | `Air display` | `"20  13  10  8  5"` | `Miller!H6` | `"20,13,10,8,5"` | comma_whitespace_presentation |
| M5 | 32 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Miller!I6` | `50` | numeric_equivalent |
| M6 | 33 | `Fuel Sample Material` | `"1 mm thick PMMA   2 cm wide"` | `Miller!E7` | `"1 mm thick pmma, 2 cm wide"` | case_comma_whitespace_presentation |
| M6 | 33 | `Fan display` | `"68   52   47   43   42   41"` | `Miller!G7` | `"68, 52, 47, 43, 42, 41"` | comma_whitespace_presentation |
| M6 | 33 | `Air display` | `"10   5   3   0"` | `Miller!H7` | `"10, 5, 3, 0"` | comma_whitespace_presentation |
| M6 | 33 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Miller!I7` | `250` | numeric_equivalent |
| M7 | 34 | `Fuel Sample Material` | `"1 cm wide PMMA 1 mm thick"` | `Miller!E8` | `"1 cm wide pmma 1 mm thick"` | case_comma_whitespace_presentation |
| M7 | 34 | `Fan display` | `"2.6   1.3   0.8  0.7  0.6  0.5; 60   49  45  44  43  42"` | `Miller!G8` | `"2.6, 1.3, 0.8,0.7,0.6,0.5; 60, 49,45,44,43,42"` | comma_whitespace_presentation |
| M7 | 34 | `Air display` | `"10   6  5  4.5  4  3"` | `Miller!H8` | `"10, 6,5,4.5,4,3"` | comma_whitespace_presentation |
| M7 | 34 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Miller!I8` | `250` | numeric_equivalent |
| M8 | 35 | `Fuel Sample Material` | `"1 cm wide PMMA 2 mm thick"` | `Miller!E9` | `"1 cm wide pmma 2 mm thick"` | case_comma_whitespace_presentation |
| M8 | 35 | `Fan display` | `"3.3   1.6  1.0   decr"` | `Miller!G9` | `"3.3, 1.6,1.0, decr"` | comma_whitespace_presentation |
| M8 | 35 | `Air display` | `"10   5>7  5 decr"` | `Miller!H9` | `"10, 5>7,5 decr"` | comma_whitespace_presentation |
| M8 | 35 | `Radiometer gain   (1000   250   50   10)` | `"50>250"` | `Miller!I9` | `"50>250"` | exact_text |
| M9 | 36 | `Fuel Sample Material` | `"1 cm wide PMMA 3 mm thick"` | `Miller!E10` | `"1 cm wide pmma 3 mm thick"` | case_comma_whitespace_presentation |
| M9 | 36 | `Fan display` | `"3.3   4.8;66  79"` | `Miller!G10` | `"3.3, 4.8;66,79"` | comma_whitespace_presentation |
| M9 | 36 | `Air display` | `"10   14"` | `Miller!H10` | `"10, 14"` | comma_whitespace_presentation |
| M9 | 36 | `Radiometer gain   (1000   250   50   10)` | `"50   250"` | `Miller!I10` | `"50, 250"` | comma_whitespace_presentation |
| M10 | 37 | `Fuel Sample Material` | `"4 mm thick   1 cm wide PMMA slab"` | `Miller!E11` | `"4 mm thick, 1 cm wide pmma slab"` | case_comma_whitespace_presentation |
| M10 | 37 | `Fan display` | `"75   105   94/91   72/69   63/61  (4.4   8.0   6.6/6.3   4.0/3.7   3/0/2.7)"` | `Miller!G11` | `"75, 105, 94/91, 72/69, 63/61  (4.4, 8.0, 6.6/6.3, 4.0/3.7, 3/0/2.7)"` | comma_whitespace_presentation |
| M10 | 37 | `Air display` | `"10  17  14  10  8"` | `Miller!H11` | `"10,17,14,10,8"` | comma_whitespace_presentation |
| M10 | 37 | `Radiometer gain   (1000   250   50   10)` | `"250  50  250"` | `Miller!I11` | `"250,50,250"` | comma_whitespace_presentation |
| M11 | 38 | `Fuel Sample Material` | `"1 cm wide PMMA 5 mm thick"` | `Miller!E12` | `"1 cm wide pmma 5 mm thick"` | case_comma_whitespace_presentation |
| M11 | 38 | `Fan display` | `"3.9  6.5  4.6  3.3  2.9  2.8; 62.5  93  77  66  63  62"` | `Miller!G12` | `"3.9,6.5,4.6,3.3,2.9,2.8; 62.5,93,77,66,63,62"` | comma_whitespace_presentation |
| M11 | 38 | `Air display` | `"10   20   15  12"` | `Miller!H12` | `"10, 20, 15,12"` | comma_whitespace_presentation |
| M11 | 38 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Miller!I12` | `250` | numeric_equivalent |
| M12 | 39 | `Fuel Sample Material` | `"2 mm thick PMMA   2 cm wide"` | `Miller!E13` | `"2 mm thick pmma, 2 cm wide"` | case_comma_whitespace_presentation |
| M12 | 39 | `Fan display` | `"41   42   41"` | `Miller!G13` | `"41, 42, 41"` | comma_whitespace_presentation |
| M12 | 39 | `Air display` | `"<1"` | `Miller!H13` | `"<1"` | exact_text |
| M12 | 39 | `Radiometer gain   (1000   250   50   10)` | `"250>50"` | `Miller!I13` | `"250>50"` | exact_text |
| M13 | 40 | `Fuel Sample Material` | `"4 mm thick PMMA   2 cm wide"` | `Miller!E14` | `"4 mm thick pmma, 2 cm wide"` | case_comma_whitespace_presentation |
| M13 | 40 | `Fan display` | `"52   47   43"` | `Miller!G14` | `"52, 47, 43"` | comma_whitespace_presentation |
| M13 | 40 | `Air display` | `"6   5   4"` | `Miller!H14` | `"6, 5, 4"` | comma_whitespace_presentation |
| M13 | 40 | `Radiometer gain   (1000   250   50   10)` | `"250>50"` | `Miller!I14` | `"250>50"` | exact_text |
| M14 | 41 | `Fuel Sample Material` | `"2mm thick PMMA   1 sided   2 cm wide"` | `Miller!E15` | `"2mm thick pmma, 1 sided, 2 cm wide"` | case_comma_whitespace_presentation |
| M14 | 41 | `Fan display` | `"pot 2.4   1.87  (54)"` | `Miller!G15` | `"pot 2.4, 1.87  (54)"` | comma_whitespace_presentation |
| M14 | 41 | `Air display` | `"10   ~8"` | `Miller!H15` | `"10, ~8"` | comma_whitespace_presentation |
| M14 | 41 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Miller!I15` | `50` | numeric_equivalent |
| M15 | 42 | `Fuel Sample Material` | `"2 cm   4 mm 1 sided PMMA slab"` | `Miller!E16` | `"2 cm, 4 mm 1 sided pmma slab"` | case_comma_whitespace_presentation |
| M15 | 42 | `Fan display` | `"ignited 10   adjusted down then up to 20   down in incrments to 15"` | `Miller!G16` | `"ignited 10, adjusted down then up to 20, down in incrments to 15"` | comma_whitespace_presentation |
| M15 | 42 | `Air display` | `"10   8  7  8  10  20  18  16  15"` | `Miller!H16` | `"10, 8,7,8,10,20,18,16,15"` | comma_whitespace_presentation |
| M15 | 42 | `Radiometer gain   (1000   250   50   10)` | `"10   250"` | `Miller!I16` | `"10, 250"` | comma_whitespace_presentation |
| M16 | 43 | `Fuel Sample Material` | `"1 mm thick PMMA   2 cm wide"` | `Miller!E17` | `"1 mm thick pmma, 2 cm wide"` | case_comma_whitespace_presentation |
| M16 | 43 | `Fan display` | `"73  57  59  48  45  43  75 (4.2  2.2  2.4  1.2  0.8  0.5  4.4)"` | `Miller!G17` | `"73,57,59,48,45,43,75 (4.2,2.2,2.4,1.2,0.8,0.5,4.4)"` | comma_whitespace_presentation |
| M16 | 43 | `Air display` | `"10  6  3  2  1  10"` | `Miller!H17` | `"10,6,3,2,1,10"` | comma_whitespace_presentation |
| M16 | 43 | `Radiometer gain   (1000   250   50   10)` | `"250  50  250"` | `Miller!I17` | `"250,50,250"` | comma_whitespace_presentation |
| M17 | 44 | `Fuel Sample Material` | `"2 cm wide PMMA 2 mm thick"` | `Miller!E18` | `"2 cm wide pmma 2 mm thick"` | case_comma_whitespace_presentation |
| M17 | 44 | `Fan display` | `"Fan pot 3.7   1.7   1.5   1.3   0.8   0.6   0.5   0.3ext"` | `Miller!G18` | `"Fan pot 3.7, 1.7, 1.5, 1.3, 0.8, 0.6, 0.5, 0.3ext"` | comma_whitespace_presentation |
| M17 | 44 | `Air display` | `"10   5   3   0ext"` | `Miller!H18` | `"10, 5, 3, 0ext"` | comma_whitespace_presentation |
| M17 | 44 | `Radiometer gain   (1000   250   50   10)` | `"250>50>250"` | `Miller!I18` | `"250>50>250"` | exact_text |
| M18 | 45 | `Fuel Sample Material` | `"2 cm wide PMMA 3 mm thick"` | `Miller!E19` | `"2 cm wide pmma 3 mm thick"` | case_comma_whitespace_presentation |
| M18 | 45 | `Fan display` | `"Fan pot 3.5   5 (brief)   3  5   2.2"` | `Miller!G19` | `"Fan pot 3.5, 5 (brief), 3,5, 2.2"` | comma_whitespace_presentation |
| M18 | 45 | `Air display` | `"10   15 (brief)   10   8"` | `Miller!H19` | `"10, 15 (brief), 10, 8"` | comma_whitespace_presentation |
| M18 | 45 | `Radiometer gain   (1000   250   50   10)` | `"50>250"` | `Miller!I19` | `"50>250"` | exact_text |
| M19 | 46 | `Fuel Sample Material` | `"4 mm thick   2 cm 2ide PMMA slab"` | `Miller!E20` | `"4 mm thick, 2 cm 2ide pmma slab"` | case_comma_whitespace_presentation |
| M19 | 46 | `Fan display` | `"75  105  94  75  77  79  59  61  57  55  53 (4.4  8.0  6.6  4.4  4.6  4.8  2.5  2.7  2.2  2.0  1.8)"` | `Miller!G20` | `"75,105,94,75,77,79,59,61,57,55,53 (4.4,8.0,6.6,4.4,4.6,4.8,2.5,2.7,2.2,2.0,1.8)"` | comma_whitespace_presentation |
| M19 | 46 | `Air display` | `"10  17  14  10  7  5"` | `Miller!H20` | `"10,17,14,10,7,5"` | comma_whitespace_presentation |
| M19 | 46 | `Radiometer gain   (1000   250   50   10)` | `"250   50   250"` | `Miller!I20` | `"250, 50, 250"` | comma_whitespace_presentation |
| M20 | 47 | `Fuel Sample Material` | `"5 mm thick PMMA   2 cm wide"` | `Miller!E21` | `"5 mm thick pmma, 2 cm wide"` | case_comma_whitespace_presentation |
| M20 | 47 | `Fan display` | `"67   58"` | `Miller!G21` | `"67, 58"` | comma_whitespace_presentation |
| M20 | 47 | `Air display` | `"10  8"` | `Miller!H21` | `"10,8"` | comma_whitespace_presentation |
| M20 | 47 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Miller!I21` | `50` | numeric_equivalent |
| O1 | 48 | `Fuel Sample Material` | `"1/4\" clear rod"` | `Olson!E2` | `"1/4\" clear rod"` | exact_text |
| O1 | 48 | `Fan display` | `"89  62  50  41"` | `Olson!G2` | `"89,62,50,41"` | comma_whitespace_presentation |
| O1 | 48 | `Air display` | `"20  10  5  2  1"` | `Olson!H2` | `"20,10,5,2,1"` | comma_whitespace_presentation |
| O1 | 48 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Olson!I2` | `50` | numeric_equivalent |
| O2 | 49 | `Fuel Sample Material` | `"1/4\" clear rod"` | `Olson!E3` | `"1/4\" clear rod"` | exact_text |
| O2 | 49 | `Fan display` | `".54 pot   0.45 pot"` | `Olson!G3` | `".54 pot, 0.45 pot"` | comma_whitespace_presentation |
| O2 | 49 | `Air display` | `"0"` | `Olson!H3` | `0` | numeric_equivalent |
| O2 | 49 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Olson!I3` | `50` | numeric_equivalent |
| O3a | 50 | `Fuel Sample Material` | `"1/4\" clear rod"` | `Olson!E4` | `"1/4\" clear rod"` | exact_text |
| O3a | 50 | `Fan display` | `""` | `Olson!G4` | `null` | both_empty |
| O3a | 50 | `Air display` | `"5  3"` | `Olson!H4` | `"5,3"` | comma_whitespace_presentation |
| O3a | 50 | `Radiometer gain   (1000   250   50   10)` | `"1000"` | `Olson!I4` | `1000` | numeric_equivalent |
| O3b | 51 | `Fuel Sample Material` | `"1/4\" clear rod"` | `Olson!E5` | `"1/4\" clear rod"` | exact_text |
| O3b | 51 | `Fan display` | `""` | `Olson!G5` | `null` | both_empty |
| O3b | 51 | `Air display` | `"5  3  2  1  low"` | `Olson!H5` | `"5,3,2,1,low"` | comma_whitespace_presentation |
| O3b | 51 | `Radiometer gain   (1000   250   50   10)` | `"1000   250"` | `Olson!I5` | `"1000, 250"` | comma_whitespace_presentation |
| O4 | 52 | `Fuel Sample Material` | `"3/8\"clear rod"` | `Olson!E6` | `"3/8\"clear rod"` | exact_text |
| O4 | 52 | `Fan display` | `"5   0.7   0.5   0.4   0.36 ext"` | `Olson!G6` | `"5, 0.7, 0.5, 0.4, 0.36 ext"` | comma_whitespace_presentation |
| O4 | 52 | `Air display` | `"5   down to ext"` | `Olson!H6` | `"5, down to ext"` | comma_whitespace_presentation |
| O4 | 52 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Olson!I6` | `250` | numeric_equivalent |
| O5a | 53 | `Fuel Sample Material` | `"1/2\" clear PMMA rod"` | `Olson!E7` | `"1/2\" clear pmma rod"` | case_comma_whitespace_presentation |
| O5a | 53 | `Fan display` | `"1.3   2.7   1.3   0.7   0.45. 4.0"` | `Olson!G7` | `"1.3, 2.7, 1.3, 0.7, 0.45. 4.0"` | comma_whitespace_presentation |
| O5a | 53 | `Air display` | `"5  10  5   2   0 (49   62   49   44   42)"` | `Olson!H7` | `"5,10,5, 2, 0 (49, 62, 49, 44, 42)"` | comma_whitespace_presentation |
| O5a | 53 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Olson!I7` | `250` | numeric_equivalent |
| O5b | 54 | `Fuel Sample Material` | `"1/2\" clear PMMA rod"` | `Olson!E8` | `"1/2\" clear pmma rod"` | case_comma_whitespace_presentation |
| O5b | 54 | `Fan display` | `"1.3"` | `Olson!G8` | `1.3` | numeric_equivalent |
| O5b | 54 | `Air display` | `"49   5 cm/s"` | `Olson!H8` | `"49, 5 cm/s"` | comma_whitespace_presentation |
| O5b | 54 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Olson!I8` | `250` | numeric_equivalent |
| O6 | 55 | `Fuel Sample Material` | `"1/4\" clear rod"` | `Olson!E9` | `"1/4\" clear rod"` | exact_text |
| O6 | 55 | `Fan display` | `"5   .36  .32  .31  .305   out .275"` | `Olson!G9` | `"5, .36,.32,.31,.305, out .275"` | comma_whitespace_presentation |
| O6 | 55 | `Air display` | `"see fan"` | `Olson!H9` | `"see fan"` | exact_text |
| O6 | 55 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Olson!I9` | `250` | numeric_equivalent |
| O7 | 56 | `Fuel Sample Material` | `"1/4\" clear rod"` | `Olson!E10` | `"1/4\" clear rod"` | exact_text |
| O7 | 56 | `Fan display` | `"5   .36  .32  ..305   blowoff fan max 10"` | `Olson!G10` | `"5, .36,.32,..305, blowoff fan max 10"` | comma_whitespace_presentation |
| O7 | 56 | `Air display` | `""` | `Olson!H10` | `null` | both_empty |
| O7 | 56 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Olson!I10` | `250` | numeric_equivalent |
| O8a | 57 | `Fuel Sample Material` | `"1/4\" clear rod"` | `Olson!E11` | `"1/4\" clear rod"` | exact_text |
| O8a | 57 | `Fan display` | `"5   .36  .32  .31   extinguished"` | `Olson!G11` | `"5, .36,.32,.31, extinguished"` | comma_whitespace_presentation |
| O8a | 57 | `Air display` | `""` | `Olson!H11` | `null` | both_empty |
| O8a | 57 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Olson!I11` | `250` | numeric_equivalent |
| O8b | 58 | `Fuel Sample Material` | `"1/4\" clear rod"` | `Olson!E12` | `"1/4\" clear rod"` | exact_text |
| O8b | 58 | `Fan display` | `"5  .36  .32  .31 blowoff fan pot 6.0"` | `Olson!G12` | `"5,.36,.32,.31 blowoff fan pot 6.0"` | comma_whitespace_presentation |
| O8b | 58 | `Air display` | `""` | `Olson!H12` | `null` | both_empty |
| O8b | 58 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Olson!I12` | `250` | numeric_equivalent |
| O9 | 59 | `Fuel Sample Material` | `"1/4\" clear rod"` | `Olson!E13` | `"1/4\" clear rod"` | exact_text |
| O9 | 59 | `Fan display` | `"5   .36  .32 blowoff pt 4.0"` | `Olson!G13` | `"5, .36,.32 blowoff pt 4.0"` | comma_whitespace_presentation |
| O9 | 59 | `Air display` | `""` | `Olson!H13` | `null` | both_empty |
| O9 | 59 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Olson!I13` | `250` | numeric_equivalent |
| O10 | 60 | `Fuel Sample Material` | `"1/4\" clear rod"` | `Olson!E14` | `"1/4\" clear rod"` | exact_text |
| O10 | 60 | `Fan display` | `"49  44  41   122 (1.3   0.7   0.4   0.36   0.32   10)"` | `Olson!G14` | `"49,44,41, 122 (1.3, 0.7, 0.4, 0.36, 0.32, 10)"` | comma_whitespace_presentation |
| O10 | 60 | `Air display` | `"5  2   0   max"` | `Olson!H14` | `"5,2, 0, max"` | comma_whitespace_presentation |
| O10 | 60 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Olson!I14` | `250` | numeric_equivalent |
| O11 | 61 | `Fuel Sample Material` | `"1/4\" black rod"` | `Olson!E15` | `"1/4\" black rod"` | exact_text |
| O11 | 61 | `Fan display` | `"ign 5   0.36   0.32   0.31   0.305   blowoff 6.0"` | `Olson!G15` | `"ign 5, 0.36, 0.32, 0.31, 0.305, blowoff 6.0"` | comma_whitespace_presentation |
| O11 | 61 | `Air display` | `"5   down then blowoff"` | `Olson!H15` | `"5, down then blowoff"` | comma_whitespace_presentation |
| O11 | 61 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Olson!I15` | `250` | numeric_equivalent |
| O12 | 62 | `Fuel Sample Material` | `"3/8\" clear rod"` | `Olson!E16` | `"3/8\" clear rod"` | exact_text |
| O12 | 62 | `Fan display` | `"pots 1.4   3   0.9   0.7"` | `Olson!G16` | `"pots 1.4, 3, 0.9, 0.7"` | comma_whitespace_presentation |
| O12 | 62 | `Air display` | `"no ign at any flow"` | `Olson!H16` | `"no ign at any flow"` | exact_text |
| O12 | 62 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Olson!I16` | `250` | numeric_equivalent |
| O13a | 63 | `Fuel Sample Material` | `"1/2\" clear PMMA rod"` | `Olson!E17` | `"1/2\" clear pmma rod"` | case_comma_whitespace_presentation |
| O13a | 63 | `Fan display` | `"1.3   0.7   0.45   0.36   0.32   0.31"` | `Olson!G17` | `"1.3, 0.7, 0.45, 0.36, 0.32, 0.31"` | comma_whitespace_presentation |
| O13a | 63 | `Air display` | `"49  44  42  41  41  40.5 (5   2   0)"` | `Olson!H17` | `"49,44,42,41,41,40.5 (5, 2, 0)"` | comma_whitespace_presentation |
| O13a | 63 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Olson!I17` | `250` | numeric_equivalent |
| O13b | 64 | `Fuel Sample Material` | `"1/2\" clear PMMA rod"` | `Olson!E18` | `"1/2\" clear pmma rod"` | case_comma_whitespace_presentation |
| O13b | 64 | `Fan display` | `"1.3   0.9"` | `Olson!G18` | `"1.3, 0.9"` | comma_whitespace_presentation |
| O13b | 64 | `Air display` | `"7   4? (49   ?)"` | `Olson!H18` | `"7, 4? (49, ?)"` | comma_whitespace_presentation |
| O13b | 64 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Olson!I18` | `250` | numeric_equivalent |
| O14 | 65 | `Fuel Sample Material` | `"1/4\" black rod"` | `Olson!E19` | `"1/4\" black rod"` | exact_text |
| O14 | 65 | `Fan display` | `"52   and down"` | `Olson!G19` | `"52, and down"` | comma_whitespace_presentation |
| O14 | 65 | `Air display` | `"5 down to ext"` | `Olson!H19` | `"5 down to ext"` | exact_text |
| O14 | 65 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Olson!I19` | `250` | numeric_equivalent |
| O15a | 66 | `Fuel Sample Material` | `"3/8\" clear rod"` | `Olson!E20` | `"3/8\" clear rod"` | exact_text |
| O15a | 66 | `Fan display` | `"57.5   47   42   41 (2.3   1.0   0.5   0.35   0.32)"` | `Olson!G20` | `"57.5, 47, 42, 41 (2.3, 1.0, 0.5, 0.35, 0.32)"` | comma_whitespace_presentation |
| O15a | 66 | `Air display` | `"5  0"` | `Olson!H20` | `"5,0"` | comma_whitespace_presentation |
| O15a | 66 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Olson!I20` | `250` | numeric_equivalent |
| O15b | 67 | `Fuel Sample Material` | `"3/8\" clear rod"` | `Olson!E21` | `"3/8\" clear rod"` | exact_text |
| O15b | 67 | `Fan display` | `"57.5   42   41   40 (2.3   0.5   0.35   0.34   0.33   0.32   0.31   0.30   0.29   0.28   0.27)"` | `Olson!G21` | `"57.5, 42, 41, 40 (2.3, 0.5, 0.35, 0.34, 0.33, 0.32, 0.31, 0.30, 0.29, 0.28, 0.27)"` | comma_whitespace_presentation |
| O15b | 67 | `Air display` | `"5   0"` | `Olson!H21` | `"5, 0"` | comma_whitespace_presentation |
| O15b | 67 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Olson!I21` | `250` | numeric_equivalent |
| O16 | 68 | `Fuel Sample Material` | `"3/8\"clear rod"` | `Olson!E22` | `"3/8\"clear rod"` | exact_text |
| O16 | 68 | `Fan display` | `"60 (2.6)"` | `Olson!G22` | `"60 (2.6)"` | exact_text |
| O16 | 68 | `Air display` | `"5"` | `Olson!H22` | `5` | numeric_equivalent |
| O16 | 68 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Olson!I22` | `250` | numeric_equivalent |
| O17 | 69 | `Fuel Sample Material` | `"1/4\" clear rod"` | `Olson!E23` | `"1/4\" clear rod"` | exact_text |
| O17 | 69 | `Fan display` | `"49   46.5   44   42  41  72   decr (1.3   1.0   0.7   0.5   0.4   4.0   decr )"` | `Olson!G23` | `"49, 46.5, 44, 42,41,72, decr (1.3, 1.0, 0.7, 0.5, 0.4, 4.0, decr )"` | comma_whitespace_presentation |
| O17 | 69 | `Air display` | `"3   0   11"` | `Olson!H23` | `"3, 0, 11"` | comma_whitespace_presentation |
| O17 | 69 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Olson!I23` | `250` | numeric_equivalent |
| O18 | 70 | `Fuel Sample Material` | `"1/4\" clear rod"` | `Olson!E24` | `"1/4\" clear rod"` | exact_text |
| O18 | 70 | `Fan display` | `"57  51  47  72  51  72  51  47 (2.3   1.5   1.0   4.0   1.5   4.0   1.5   1.0)"` | `Olson!G24` | `"57,51,47,72,51,72,51,47 (2.3, 1.5, 1.0, 4.0, 1.5, 4.0, 1.5, 1.0)"` | comma_whitespace_presentation |
| O18 | 70 | `Air display` | `"5  2  0  11  2  11  2  0"` | `Olson!H24` | `"5,2,0,11,2,11,2,0"` | comma_whitespace_presentation |
| O18 | 70 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Olson!I24` | `250` | numeric_equivalent |
| O19 | 71 | `Fuel Sample Material` | `"1/4\" clear rod"` | `Olson!E25` | `"1/4\" clear rod"` | exact_text |
| O19 | 71 | `Fan display` | `"52   and down"` | `Olson!G25` | `"52, and down"` | comma_whitespace_presentation |
| O19 | 71 | `Air display` | `"5 down to ext"` | `Olson!H25` | `"5 down to ext"` | exact_text |
| O19 | 71 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Olson!I25` | `250` | numeric_equivalent |
| O20 | 72 | `Fuel Sample Material` | `"1/4\" clear rod"` | `Olson!E26` | `"1/4\" clear rod"` | exact_text |
| O20 | 72 | `Fan display` | `"49 (1.3 pot)   pots 7   8  9   10"` | `Olson!G26` | `"49 (1.3 pot), pots 7, 8,9, 10"` | comma_whitespace_presentation |
| O20 | 72 | `Air display` | `"5   8    incr to max 38.5"` | `Olson!H26` | `"5, 8,  incr to max 38.5"` | comma_whitespace_presentation |
| O20 | 72 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Olson!I26` | `50` | numeric_equivalent |
| O21 | 73 | `Fuel Sample Material` | `"3/8\" clear rod"` | `Olson!E27` | `"3/8\" clear rod"` | exact_text |
| O21 | 73 | `Fan display` | `"46 (pot 0.8)    pot 7   10"` | `Olson!G27` | `"46 (pot 0.8),  pot 7, 10"` | comma_whitespace_presentation |
| O21 | 73 | `Air display` | `"incr to 28"` | `Olson!H27` | `"incr to 28"` | exact_text |
| O21 | 73 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Olson!I27` | `50` | numeric_equivalent |
| O22 | 74 | `Fuel Sample Material` | `"1/2\" clear rod "` | `Olson!E28` | `"1/2\" clear rod "` | exact_text |
| O22 | 74 | `Fan display` | `"49 (pot 1.1)   blowoff pot 5   out at fan 87"` | `Olson!G28` | `"49 (pot 1.1), blowoff pot 5, out at fan 87"` | comma_whitespace_presentation |
| O22 | 74 | `Air display` | `"4 incr to 26.5"` | `Olson!H28` | `"4 incr to 26.5"` | exact_text |
| O22 | 74 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Olson!I28` | `50` | numeric_equivalent |
| P1 | 75 | `Fuel Sample Material` | `"1/4\" black rod"` | `Fernandez-Pello!E2` | `"1/4\" black rod"` | exact_text |
| P1 | 75 | `Fan display` | `""` | `Fernandez-Pello!G2` | `null` | both_empty |
| P1 | 75 | `Air display` | `"5  2   slow decr to ext"` | `Fernandez-Pello!H2` | `"5,2, slow decr to ext"` | comma_whitespace_presentation |
| P1 | 75 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Fernandez-Pello!I2` | `250` | numeric_equivalent |
| P2 | 76 | `Fuel Sample Material` | `"1/4\" black rod"` | `Fernandez-Pello!E3` | `"1/4\" black rod"` | exact_text |
| P2 | 76 | `Fan display` | `""` | `Fernandez-Pello!G3` | `null` | both_empty |
| P2 | 76 | `Air display` | `"5   2.5   2 (pot .9   .5   .35.  .33)"` | `Fernandez-Pello!H3` | `"5, 2.5, 2 (pot .9, .5, .35.,.33)"` | comma_whitespace_presentation |
| P2 | 76 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Fernandez-Pello!I3` | `250` | numeric_equivalent |
| P3a | 77 | `Fuel Sample Material` | `"1/4\" clear rod"` | `Fernandez-Pello!E4` | `"1/4\" clear rod"` | exact_text |
| P3a | 77 | `Fan display` | `""` | `Fernandez-Pello!G4` | `null` | both_empty |
| P3a | 77 | `Air display` | `"5   2.5 (1.15   .5   .35   .33. .32   .315   .31   .3)"` | `Fernandez-Pello!H4` | `"5, 2.5 (1.15, .5, .35, .33. .32, .315, .31, .3)"` | comma_whitespace_presentation |
| P3a | 77 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Fernandez-Pello!I4` | `250` | numeric_equivalent |
| P3b | 78 | `Fuel Sample Material` | `"1/4 clear rod"` | `Fernandez-Pello!E5` | `"1/4 clear rod"` | exact_text |
| P3b | 78 | `Fan display` | `""` | `Fernandez-Pello!G5` | `null` | both_empty |
| P3b | 78 | `Air display` | `"5   very low (0.85   0.32   0.31   0.305   0.30   0.295)"` | `Fernandez-Pello!H5` | `"5, very low (0.85, 0.32, 0.31, 0.305, 0.30, 0.295)"` | comma_whitespace_presentation |
| P3b | 78 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Fernandez-Pello!I5` | `250` | numeric_equivalent |
| P4 | 79 | `Fuel Sample Material` | `"3/8\" black rod"` | `Fernandez-Pello!E6` | `"3/8\" black rod"` | exact_text |
| P4 | 79 | `Fan display` | `"48   41"` | `Fernandez-Pello!G6` | `"48, 41"` | comma_whitespace_presentation |
| P4 | 79 | `Air display` | `"5   pots 0.4   0.36   0.32   0.308   .3   off"` | `Fernandez-Pello!H6` | `"5, pots 0.4, 0.36, 0.32, 0.308, .3, off"` | comma_whitespace_presentation |
| P4 | 79 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Fernandez-Pello!I6` | `50` | numeric_equivalent |
| P5 | 80 | `Fuel Sample Material` | `"0.5\" black rod"` | `Fernandez-Pello!E7` | `"0.5\" black rod"` | exact_text |
| P5 | 80 | `Fan display` | `"Fan pot 1.5 (5cm/s)   0.9   0.4   0.36   0.32   0.308   0.3   0.29   0.28   0 ext"` | `Fernandez-Pello!G7` | `"Fan pot 1.5 (5cm/s), 0.9, 0.4, 0.36, 0.32, 0.308, 0.3, 0.29, 0.28, 0 ext"` | comma_whitespace_presentation |
| P5 | 80 | `Air display` | `"5 down to ext"` | `Fernandez-Pello!H7` | `"5 down to ext"` | exact_text |
| P5 | 80 | `Radiometer gain   (1000   250   50   10)` | `"250>50"` | `Fernandez-Pello!I7` | `"250>50"` | exact_text |
| P6 | 81 | `Fuel Sample Material` | `"1/4\" black rod"` | `Fernandez-Pello!E8` | `"1/4\" black rod"` | exact_text |
| P6 | 81 | `Fan display` | `"48   41"` | `Fernandez-Pello!G8` | `"48, 41"` | comma_whitespace_presentation |
| P6 | 81 | `Air display` | `"5   pots 0.4   0.36   0.32   0.31   off"` | `Fernandez-Pello!H8` | `"5, pots 0.4, 0.36, 0.32, 0.31, off"` | comma_whitespace_presentation |
| P6 | 81 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Fernandez-Pello!I8` | `50` | numeric_equivalent |
| P8 | 82 | `Fuel Sample Material` | `"3/8\" black rod"` | `Fernandez-Pello!E9` | `"3/8\" black rod"` | exact_text |
| P8 | 82 | `Fan display` | `"48   62   75"` | `Fernandez-Pello!G9` | `"48, 62, 75"` | comma_whitespace_presentation |
| P8 | 82 | `Air display` | `"5   would not stay lit   10   15 ibid"` | `Fernandez-Pello!H9` | `"5, would not stay lit, 10, 15 ibid"` | comma_whitespace_presentation |
| P8 | 82 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Fernandez-Pello!I9` | `50` | numeric_equivalent |
| P9 | 83 | `Fuel Sample Material` | `"0.5\" black rod"` | `Fernandez-Pello!E10` | `"0.5\" black rod"` | exact_text |
| P9 | 83 | `Fan display` | `"Fan pot 1.5 (5cm/s)   0.9   0.4   0.36   0.32   0.3   0.28 ext"` | `Fernandez-Pello!G10` | `"Fan pot 1.5 (5cm/s), 0.9, 0.4, 0.36, 0.32, 0.3, 0.28 ext"` | comma_whitespace_presentation |
| P9 | 83 | `Air display` | `"5 down to ext"` | `Fernandez-Pello!H10` | `"5 down to ext"` | exact_text |
| P9 | 83 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Fernandez-Pello!I10` | `50` | numeric_equivalent |
| P10 | 84 | `Fuel Sample Material` | `"1/4\" black rod"` | `Fernandez-Pello!E11` | `"1/4\" black rod"` | exact_text |
| P10 | 84 | `Fan display` | `"48   41"` | `Fernandez-Pello!G11` | `"48, 41"` | comma_whitespace_presentation |
| P10 | 84 | `Air display` | `"5   pots 0.4   0.36   0.32   0.31   0.30 extinguished"` | `Fernandez-Pello!H11` | `"5, pots 0.4, 0.36, 0.32, 0.31, 0.30 extinguished"` | comma_whitespace_presentation |
| P10 | 84 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Fernandez-Pello!I11` | `50` | numeric_equivalent |
| P12 | 85 | `Fuel Sample Material` | `"3/8\" black rod"` | `Fernandez-Pello!E12` | `"3/8\" black rod"` | exact_text |
| P12 | 85 | `Fan display` | `"60  52  48  44.5  42  41.5  41 (2.6  1.6  1.2  .75  .5  .4  .36  0.34)"` | `Fernandez-Pello!G12` | `"60,52,48,44.5,42,41.5,41 (2.6,1.6,1.2,.75,.5,.4,.36,0.34)"` | comma_whitespace_presentation |
| P12 | 85 | `Air display` | `"5   3  2  1   0.5   lower"` | `Fernandez-Pello!H12` | `"5, 3,2,1, 0.5, lower"` | comma_whitespace_presentation |
| P12 | 85 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Fernandez-Pello!I12` | `250` | numeric_equivalent |
| P13a | 86 | `Fuel Sample Material` | `"0.5\" black rod"` | `Fernandez-Pello!E13` | `"0.5\" black rod"` | exact_text |
| P13a | 86 | `Fan display` | `"Fan pot 1.1 (5cm/s)   0.4   0.36   0.32   0.3   0.28   0.26   0 ext"` | `Fernandez-Pello!G13` | `"Fan pot 1.1 (5cm/s), 0.4, 0.36, 0.32, 0.3, 0.28, 0.26, 0 ext"` | comma_whitespace_presentation |
| P13a | 86 | `Air display` | `"5 down to ext"` | `Fernandez-Pello!H13` | `"5 down to ext"` | exact_text |
| P13a | 86 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Fernandez-Pello!I13` | `50` | numeric_equivalent |
| P13b | 87 | `Fuel Sample Material` | `"0.5\" black rod"` | `Fernandez-Pello!E14` | `"0.5\" black rod"` | exact_text |
| P13b | 87 | `Fan display` | `"Fan pot 1.3 (5cm/s)   0.4   0.36   0.32 ext"` | `Fernandez-Pello!G14` | `"Fan pot 1.3 (5cm/s), 0.4, 0.36, 0.32 ext"` | comma_whitespace_presentation |
| P13b | 87 | `Air display` | `"5 down to ext"` | `Fernandez-Pello!H14` | `"5 down to ext"` | exact_text |
| P13b | 87 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Fernandez-Pello!I14` | `50` | numeric_equivalent |
| P14 | 88 | `Fuel Sample Material` | `"1/4 blac rod"` | `Fernandez-Pello!E15` | `"1/4 blac rod"` | exact_text |
| P14 | 88 | `Fan display` | `"46   41"` | `Fernandez-Pello!G15` | `"46, 41"` | comma_whitespace_presentation |
| P14 | 88 | `Air display` | `"5   low (.85   .4   .32)"` | `Fernandez-Pello!H15` | `"5, low (.85, .4, .32)"` | comma_whitespace_presentation |
| P14 | 88 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Fernandez-Pello!I15` | `250` | numeric_equivalent |
| P15 | 89 | `Fuel Sample Material` | `"1/4 black rod"` | `Fernandez-Pello!E16` | `"1/4 black rod"` | exact_text |
| P15 | 89 | `Fan display` | `"46   41"` | `Fernandez-Pello!G16` | `"46, 41"` | comma_whitespace_presentation |
| P15 | 89 | `Air display` | `"5   (0.36)"` | `Fernandez-Pello!H16` | `"5, (0.36)"` | comma_whitespace_presentation |
| P15 | 89 | `Radiometer gain   (1000   250   50   10)` | `"250   50"` | `Fernandez-Pello!I16` | `"250, 50"` | comma_whitespace_presentation |
| P16 | 90 | `Fuel Sample Material` | `"1/4\" black rod"` | `Fernandez-Pello!E17` | `"1/4\" black rod"` | exact_text |
| P16 | 90 | `Fan display` | `"49  62  44  41.5  41 (pots 1.3   2.8   0.7   0.4   0.36   0.32)"` | `Fernandez-Pello!G17` | `"49,62,44,41.5,41 (pots 1.3, 2.8, 0.7, 0.4, 0.36, 0.32)"` | comma_whitespace_presentation |
| P16 | 90 | `Air display` | `"5  8  2  low"` | `Fernandez-Pello!H17` | `"5,8,2,low"` | comma_whitespace_presentation |
| P16 | 90 | `Radiometer gain   (1000   250   50   10)` | `"250  50"` | `Fernandez-Pello!I17` | `"250,50"` | comma_whitespace_presentation |
| P17 | 91 | `Fuel Sample Material` | `"1/4\"  black rod"` | `Fernandez-Pello!E18` | `"1/4\"  black rod"` | exact_text |
| P17 | 91 | `Fan display` | `"60  52  48  233  48  41 (2.6   1.6   1.2   10   1.2   0.36   0.34)"` | `Fernandez-Pello!G18` | `"60,52,48,233,48,41 (2.6, 1.6, 1.2, 10, 1.2, 0.36, 0.34)"` | comma_whitespace_presentation |
| P17 | 91 | `Air display` | `"5   3   2   22   2   low"` | `Fernandez-Pello!H18` | `"5, 3, 2, 22, 2, low"` | comma_whitespace_presentation |
| P17 | 91 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Fernandez-Pello!I18` | `250` | numeric_equivalent |
| P18 | 92 | `Fuel Sample Material` | `"1/4\" black rod"` | `Fernandez-Pello!E19` | `"1/4\" black rod"` | exact_text |
| P18 | 92 | `Fan display` | `"55  47  etc (pot 1  2  1  2   etc)"` | `Fernandez-Pello!G19` | `"55,47,etc (pot 1,2,1,2, etc)"` | comma_whitespace_presentation |
| P18 | 92 | `Air display` | `"2  0  2  0  etc"` | `Fernandez-Pello!H19` | `"2,0,2,0,etc"` | comma_whitespace_presentation |
| P18 | 92 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Fernandez-Pello!I19` | `250` | numeric_equivalent |
| P19 | 93 | `Fuel Sample Material` | `"1/4\" black rod"` | `Fernandez-Pello!E20` | `"1/4\" black rod"` | exact_text |
| P19 | 93 | `Fan display` | `"49  62  44  41.5  122   41 (pots 1.3   2.8   0.7   0.4   0.36   10.   0.32)"` | `Fernandez-Pello!G20` | `"49,62,44,41.5,122, 41 (pots 1.3, 2.8, 0.7, 0.4, 0.36, 10., 0.32)"` | comma_whitespace_presentation |
| P19 | 93 | `Air display` | `"5  8  2  max   0"` | `Fernandez-Pello!H20` | `"5,8,2,max, 0"` | comma_whitespace_presentation |
| P19 | 93 | `Radiometer gain   (1000   250   50   10)` | `"250   50"` | `Fernandez-Pello!I20` | `"250, 50"` | comma_whitespace_presentation |
| P20 | 94 | `Fuel Sample Material` | `"1/4\" black rod"` | `Fernandez-Pello!E21` | `"1/4\" black rod"` | exact_text |
| P20 | 94 | `Fan display` | `"55  47  etc (pot 1  2  1  2   etc)"` | `Fernandez-Pello!G21` | `"55,47,etc (pot 1,2,1,2, etc)"` | comma_whitespace_presentation |
| P20 | 94 | `Air display` | `"2  0  2  0  etc"` | `Fernandez-Pello!H21` | `"2,0,2,0,etc"` | comma_whitespace_presentation |
| P20 | 94 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Fernandez-Pello!I21` | `50` | numeric_equivalent |
| P21a | 95 | `Fuel Sample Material` | `"1/4 black rod"` | `Fernandez-Pello!E22` | `"1/4 black rod"` | exact_text |
| P21a | 95 | `Fan display` | `"46"` | `Fernandez-Pello!G22` | `46` | numeric_equivalent |
| P21a | 95 | `Air display` | `"5"` | `Fernandez-Pello!H22` | `5` | numeric_equivalent |
| P21a | 95 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Fernandez-Pello!I22` | `250` | numeric_equivalent |
| P21b | 96 | `Fuel Sample Material` | `"1/4\" black rod"` | `Fernandez-Pello!E23` | `"1/4\" black rod"` | exact_text |
| P21b | 96 | `Fan display` | `"46"` | `Fernandez-Pello!G23` | `46` | numeric_equivalent |
| P21b | 96 | `Air display` | `"5"` | `Fernandez-Pello!H23` | `5` | numeric_equivalent |
| P21b | 96 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `Fernandez-Pello!I23` | `250` | numeric_equivalent |
| P22a | 97 | `Fuel Sample Material` | `"3/8\" black rod"` | `Fernandez-Pello!E24` | `"3/8\" black rod"` | exact_text |
| P22a | 97 | `Fan display` | `"5   0.36   0.32 ext after some time"` | `Fernandez-Pello!G24` | `"5, 0.36, 0.32 ext after some time"` | comma_whitespace_presentation |
| P22a | 97 | `Air display` | `"5   down to ext"` | `Fernandez-Pello!H24` | `"5, down to ext"` | comma_whitespace_presentation |
| P22a | 97 | `Radiometer gain   (1000   250   50   10)` | `"250>50"` | `Fernandez-Pello!I24` | `"250>50"` | exact_text |
| P22b | 98 | `Fuel Sample Material` | `"3/8\" black rod"` | `Fernandez-Pello!E25` | `"3/8\" black rod"` | exact_text |
| P22b | 98 | `Fan display` | `"5   p.36   0.34   0.33   0.32   0.31 ext"` | `Fernandez-Pello!G25` | `"5, p.36, 0.34, 0.33, 0.32, 0.31 ext"` | comma_whitespace_presentation |
| P22b | 98 | `Air display` | `"5 down to ext"` | `Fernandez-Pello!H25` | `"5 down to ext"` | exact_text |
| P22b | 98 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Fernandez-Pello!I25` | `50` | numeric_equivalent |
| P23 | 99 | `Fuel Sample Material` | `"3/8\" black rod"` | `Fernandez-Pello!E26` | `"3/8\" black rod"` | exact_text |
| P23 | 99 | `Fan display` | `"55  47  etc (pot 1  2  1  2   etc)"` | `Fernandez-Pello!G26` | `"55,47,etc (pot 1,2,1,2, etc)"` | comma_whitespace_presentation |
| P23 | 99 | `Air display` | `"2  0  2  0  etc"` | `Fernandez-Pello!H26` | `"2,0,2,0,etc"` | comma_whitespace_presentation |
| P23 | 99 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Fernandez-Pello!I26` | `50` | numeric_equivalent |
| P24 | 100 | `Fuel Sample Material` | `"3/8\" black rod"` | `Fernandez-Pello!E27` | `"3/8\" black rod"` | exact_text |
| P24 | 100 | `Fan display` | `"55  47  etc (pot 1  2  1  2   etc)"` | `Fernandez-Pello!G27` | `"55,47,etc (pot 1,2,1,2, etc)"` | comma_whitespace_presentation |
| P24 | 100 | `Air display` | `"2  0  2  0  etc"` | `Fernandez-Pello!H27` | `"2,0,2,0,etc"` | comma_whitespace_presentation |
| P24 | 100 | `Radiometer gain   (1000   250   50   10)` | `"250>50"` | `Fernandez-Pello!I27` | `"250>50"` | exact_text |
| P25 | 101 | `Fuel Sample Material` | `"3/8\" clear rod"` | `Fernandez-Pello!E28` | `"3/8\" clear rod"` | exact_text |
| P25 | 101 | `Fan display` | `"5   p.36   0.34   0.33   0.32   0.31 ext"` | `Fernandez-Pello!G28` | `"5, p.36, 0.34, 0.33, 0.32, 0.31 ext"` | comma_whitespace_presentation |
| P25 | 101 | `Air display` | `"5 down to ext"` | `Fernandez-Pello!H28` | `"5 down to ext"` | exact_text |
| P25 | 101 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `Fernandez-Pello!I28` | `50` | numeric_equivalent |
| T1 | 102 | `Fuel Sample Material` | `"2 cm SIBAL"` | `T'ien!E2` | `"SIBAL 2 cm"` | word_order_only_reviewed |
| T1 | 102 | `Fan display` | `"80"` | `T'ien!G2` | `80` | numeric_equivalent |
| T1 | 102 | `Air display` | `"10"` | `T'ien!H2` | `10` | numeric_equivalent |
| T1 | 102 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `T'ien!I2` | `50` | numeric_equivalent |
| T2 | 103 | `Fuel Sample Material` | `"2 cm SIBAL"` | `T'ien!E3` | `"SIBAL 2 cm"` | word_order_only_reviewed |
| T2 | 103 | `Fan display` | `"80   59   55"` | `T'ien!G3` | `"80, 59, 55"` | comma_whitespace_presentation |
| T2 | 103 | `Air display` | `"9   5   4"` | `T'ien!H3` | `"9, 5, 4"` | comma_whitespace_presentation |
| T2 | 103 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `T'ien!I3` | `50` | numeric_equivalent |
| T3 | 104 | `Fuel Sample Material` | `"4 cm spherical section"` | `T'ien!E4` | `"4 cm spherical section"` | exact_text |
| T3 | 104 | `Fan display` | `"63"` | `T'ien!G4` | `63` | numeric_equivalent |
| T3 | 104 | `Air display` | `"10"` | `T'ien!H4` | `10` | numeric_equivalent |
| T3 | 104 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `T'ien!I4` | `250` | numeric_equivalent |
| T4 | 105 | `Fuel Sample Material` | `"2 cm SIBAL"` | `T'ien!E5` | `"SIBAL 2 cm"` | word_order_only_reviewed |
| T4 | 105 | `Fan display` | `"80   46"` | `T'ien!G5` | `"80, 46"` | comma_whitespace_presentation |
| T4 | 105 | `Air display` | `"9  1"` | `T'ien!H5` | `"9,1"` | comma_whitespace_presentation |
| T4 | 105 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `T'ien!I5` | `50` | numeric_equivalent |
| T5 | 106 | `Fuel Sample Material` | `"2 cm SIBAL"` | `T'ien!E6` | `"2 cm SIBAL"` | exact_text |
| T5 | 106 | `Fan display` | `"2.72   0.50   0.42"` | `T'ien!G6` | `"2.72, 0.50, 0.42"` | comma_whitespace_presentation |
| T5 | 106 | `Air display` | `"10   2   1"` | `T'ien!H6` | `"10, 2, 1"` | comma_whitespace_presentation |
| T5 | 106 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `T'ien!I6` | `50` | numeric_equivalent |
| T6 | 107 | `Fuel Sample Material` | `"2 cm SIBAL"` | `T'ien!E7` | `"2 cm SIBAL"` | exact_text |
| T6 | 107 | `Fan display` | `""` | `T'ien!G7` | `null` | both_empty |
| T6 | 107 | `Air display` | `"5  2  1   <1"` | `T'ien!H7` | `"5,2,1, <1"` | comma_whitespace_presentation |
| T6 | 107 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `T'ien!I7` | `50` | numeric_equivalent |
| T7 | 108 | `Fuel Sample Material` | `"4 cm spherical section"` | `T'ien!E8` | `"4 cm spherical section"` | exact_text |
| T7 | 108 | `Fan display` | `"3.4   67"` | `T'ien!G8` | `"3.4, 67"` | comma_whitespace_presentation |
| T7 | 108 | `Air display` | `"10   5  3  1   decr"` | `T'ien!H8` | `"10, 5,3,1, decr"` | comma_whitespace_presentation |
| T7 | 108 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `T'ien!I8` | `250` | numeric_equivalent |
| T9 | 109 | `Fuel Sample Material` | `"2 cm SIBAL"` | `T'ien!E9` | `"2 cm SIBAL"` | exact_text |
| T9 | 109 | `Fan display` | `"pot 2.5"` | `T'ien!G9` | `"pot 2.5"` | exact_text |
| T9 | 109 | `Air display` | `"10"` | `T'ien!H9` | `10` | numeric_equivalent |
| T9 | 109 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `T'ien!I9` | `250` | numeric_equivalent |
| T10 | 110 | `Fuel Sample Material` | `"2 cm SIBAL"` | `T'ien!E10` | `"2 cm SIBAL"` | exact_text |
| T10 | 110 | `Fan display` | `"pot 1.1"` | `T'ien!G10` | `"pot 1.1"` | exact_text |
| T10 | 110 | `Air display` | `"5"` | `T'ien!H10` | `5` | numeric_equivalent |
| T10 | 110 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `T'ien!I10` | `250` | numeric_equivalent |
| T11 | 111 | `Fuel Sample Material` | `"2 cm SIBAL"` | `T'ien!E11` | `"2 cm SIBAL"` | exact_text |
| T11 | 111 | `Fan display` | `"48"` | `T'ien!G11` | `48` | numeric_equivalent |
| T11 | 111 | `Air display` | `"5"` | `T'ien!H11` | `5` | numeric_equivalent |
| T11 | 111 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `T'ien!I11` | `250` | numeric_equivalent |
| T12 | 112 | `Fuel Sample Material` | `"2 cm SIBAL"` | `T'ien!E12` | `"2 cm SIBAL"` | exact_text |
| T12 | 112 | `Fan display` | `"pot 1.1"` | `T'ien!G12` | `"pot 1.1"` | exact_text |
| T12 | 112 | `Air display` | `"5"` | `T'ien!H12` | `5` | numeric_equivalent |
| T12 | 112 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `T'ien!I12` | `250` | numeric_equivalent |
| T13 | 113 | `Fuel Sample Material` | `"2 cm SIBAL"` | `T'ien!E13` | `"2 cm SIBAL"` | exact_text |
| T13 | 113 | `Fan display` | `""` | `T'ien!G13` | `null` | both_empty |
| T13 | 113 | `Air display` | `"5  1"` | `T'ien!H13` | `"5,1"` | comma_whitespace_presentation |
| T13 | 113 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `T'ien!I13` | `50` | numeric_equivalent |
| T14 | 114 | `Fuel Sample Material` | `"2 cm SIBAL"` | `T'ien!E14` | `"2 cm SIBAL"` | exact_text |
| T14 | 114 | `Fan display` | `""` | `T'ien!G14` | `null` | both_empty |
| T14 | 114 | `Air display` | `"5  3"` | `T'ien!H14` | `"5,3"` | comma_whitespace_presentation |
| T14 | 114 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `T'ien!I14` | `250` | numeric_equivalent |
| T15 | 115 | `Fuel Sample Material` | `"2 cm SIBAL"` | `T'ien!E15` | `"SIBAL 2 cm"` | word_order_only_reviewed |
| T15 | 115 | `Fan display` | `"80122"` | `T'ien!G15` | `80122` | numeric_equivalent |
| T15 | 115 | `Air display` | `"9   29"` | `T'ien!H15` | `"9, 29"` | comma_whitespace_presentation |
| T15 | 115 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `T'ien!I15` | `50` | numeric_equivalent |
| T16 | 116 | `Fuel Sample Material` | `"2 cm SIBAL"` | `T'ien!E16` | `"2 cm SIBAL"` | exact_text |
| T16 | 116 | `Fan display` | `""` | `T'ien!G16` | `null` | both_empty |
| T16 | 116 | `Air display` | `"5  3"` | `T'ien!H16` | `"5,3"` | comma_whitespace_presentation |
| T16 | 116 | `Radiometer gain   (1000   250   50   10)` | `"50"` | `T'ien!I16` | `50` | numeric_equivalent |
| T17 | 117 | `Fuel Sample Material` | `"2 cm SIBAL"` | `T'ien!E17` | `"2 cm SIBAL"` | exact_text |
| T17 | 117 | `Fan display` | `""` | `T'ien!G17` | `null` | both_empty |
| T17 | 117 | `Air display` | `"6   53"` | `T'ien!H17` | `"6, 53"` | comma_whitespace_presentation |
| T17 | 117 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `T'ien!I17` | `250` | numeric_equivalent |
| T18 | 118 | `Fuel Sample Material` | `"2 cm SIBAL"` | `T'ien!E18` | `"2 cm SIBAL"` | exact_text |
| T18 | 118 | `Fan display` | `""` | `T'ien!G18` | `null` | both_empty |
| T18 | 118 | `Air display` | `"5  2"` | `T'ien!H18` | `"5,2"` | comma_whitespace_presentation |
| T18 | 118 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `T'ien!I18` | `250` | numeric_equivalent |
| T19 | 119 | `Fuel Sample Material` | `"1 cm SIBAL"` | `T'ien!E19` | `"1 cm SIBAL"` | exact_text |
| T19 | 119 | `Fan display` | `"68.5   pot 3.6"` | `T'ien!G19` | `"68.5, pot 3.6"` | comma_whitespace_presentation |
| T19 | 119 | `Air display` | `"11"` | `T'ien!H19` | `11` | numeric_equivalent |
| T19 | 119 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `T'ien!I19` | `250` | numeric_equivalent |
| T20 | 120 | `Fuel Sample Material` | `"1 cm SIBAL"` | `T'ien!E20` | `"1 cm SIBAL"` | exact_text |
| T20 | 120 | `Fan display` | `"3.6   0.9"` | `T'ien!G20` | `"3.6, 0.9"` | comma_whitespace_presentation |
| T20 | 120 | `Air display` | `"11   3"` | `T'ien!H20` | `"11, 3"` | comma_whitespace_presentation |
| T20 | 120 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `T'ien!I20` | `250` | numeric_equivalent |
| T21 | 121 | `Fuel Sample Material` | `"1 cm SIBAL"` | `T'ien!E21` | `"1 cm SIBAL"` | exact_text |
| T21 | 121 | `Fan display` | `"1.6 pot   52"` | `T'ien!G21` | `"1.6 pot, 52"` | comma_whitespace_presentation |
| T21 | 121 | `Air display` | `"11   max(47)"` | `T'ien!H21` | `"11, max(47)"` | comma_whitespace_presentation |
| T21 | 121 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `T'ien!I21` | `250` | numeric_equivalent |
| T22 | 122 | `Fuel Sample Material` | `"1 cm SIBAL"` | `T'ien!E22` | `"1 cm SIBAL"` | exact_text |
| T22 | 122 | `Fan display` | `"3.4   1.7"` | `T'ien!G22` | `"3.4, 1.7"` | comma_whitespace_presentation |
| T22 | 122 | `Air display` | `"10   5"` | `T'ien!H22` | `"10, 5"` | comma_whitespace_presentation |
| T22 | 122 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `T'ien!I22` | `250` | numeric_equivalent |
| T23 | 123 | `Fuel Sample Material` | `"2 cm Sibal   moved igniter"` | `T'ien!E23` | `"2 cm Sibal, moved igniter"` | comma_whitespace_presentation |
| T23 | 123 | `Fan display` | `"3.3   66"` | `T'ien!G23` | `"3.3, 66"` | comma_whitespace_presentation |
| T23 | 123 | `Air display` | `"10"` | `T'ien!H23` | `10` | numeric_equivalent |
| T23 | 123 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `T'ien!I23` | `250` | numeric_equivalent |
| T24 | 124 | `Fuel Sample Material` | `"1 cm SIBAL   top side ign"` | `T'ien!E24` | `"1 cm SIBAL, top side ign"` | comma_whitespace_presentation |
| T24 | 124 | `Fan display` | `"3.3 66"` | `T'ien!G24` | `"3.3 66"` | exact_text |
| T24 | 124 | `Air display` | `"10"` | `T'ien!H24` | `10` | numeric_equivalent |
| T24 | 124 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `T'ien!I24` | `250` | numeric_equivalent |
| T25 | 125 | `Fuel Sample Material` | `"2 cm SIBAL"` | `T'ien!E25` | `"SIBAL 2 cm"` | word_order_only_reviewed |
| T25 | 125 | `Fan display` | `"53   45"` | `T'ien!G25` | `"53, 45"` | comma_whitespace_presentation |
| T25 | 125 | `Air display` | `"5   2.5"` | `T'ien!H25` | `"5, 2.5"` | comma_whitespace_presentation |
| T25 | 125 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `T'ien!I25` | `250` | numeric_equivalent |
| T26 | 126 | `Fuel Sample Material` | `"2 cm SIBAL"` | `T'ien!E26` | `"SIBAL 2 cm"` | word_order_only_reviewed |
| T26 | 126 | `Fan display` | `"53   45"` | `T'ien!G26` | `"53, 45"` | comma_whitespace_presentation |
| T26 | 126 | `Air display` | `"5   2.5"` | `T'ien!H26` | `"5, 2.5"` | comma_whitespace_presentation |
| T26 | 126 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `T'ien!I26` | `250` | numeric_equivalent |
| T27 | 127 | `Fuel Sample Material` | `"1 cm SIBAL"` | `T'ien!E27` | `"1 cm SIBAL"` | exact_text |
| T27 | 127 | `Fan display` | `"53   45"` | `T'ien!G27` | `"53, 45"` | comma_whitespace_presentation |
| T27 | 127 | `Air display` | `"5   2"` | `T'ien!H27` | `"5, 2"` | comma_whitespace_presentation |
| T27 | 127 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `T'ien!I27` | `250` | numeric_equivalent |
| T28a | 128 | `Fuel Sample Material` | `"1 cm SIBAL"` | `T'ien!E28` | `"1 cm SIBAL"` | exact_text |
| T28a | 128 | `Fan display` | `"53"` | `T'ien!G28` | `53` | numeric_equivalent |
| T28a | 128 | `Air display` | `"5"` | `T'ien!H28` | `5` | numeric_equivalent |
| T28a | 128 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `T'ien!I28` | `250` | numeric_equivalent |
| T28b | 129 | `Fuel Sample Material` | `"1 cm SIBAL"` | `T'ien!E29` | `"1 cm SIBAL"` | exact_text |
| T28b | 129 | `Fan display` | `"53"` | `T'ien!G29` | `53` | numeric_equivalent |
| T28b | 129 | `Air display` | `"5"` | `T'ien!H29` | `5` | numeric_equivalent |
| T28b | 129 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `T'ien!I29` | `250` | numeric_equivalent |
| T29 | 130 | `Fuel Sample Material` | `"1 cm SIBAL"` | `T'ien!E30` | `"1 cm SIBAL"` | exact_text |
| T29 | 130 | `Fan display` | `"53   43"` | `T'ien!G30` | `"53, 43"` | comma_whitespace_presentation |
| T29 | 130 | `Air display` | `"5   2(?)"` | `T'ien!H30` | `"5, 2(?)"` | comma_whitespace_presentation |
| T29 | 130 | `Radiometer gain   (1000   250   50   10)` | `"250"` | `T'ien!I30` | `250` | numeric_equivalent |

## Repeated sample identifiers

FAQ p. 1 paragraphs 15–16 explains a/b as multiple runs on the same sample on the same day, and that samples can be reused. These exact `(sheet, sample text)` groups recur in the source. Do not deduplicate by sample, strip suffixes or assume statistical independence.

| Worksheet | Sample ID | Tests / CSV rows | Workbook sample cells |
| --- | --- | --- | --- |
| `Bhattacharjee` | `"174m"` | B14 / 15; B21 / 22 | D15, D22 |
| `Bhattacharjee` | `"176m"` | B18 / 19; B22 / 23 | D19, D23 |
| `Olson` | `"205M"` | O3a / 50; O3b / 51 | D4, D5 |
| `Olson` | `"220m"` | O5a / 53; O5b / 54; O22 / 74 | D7, D8, D28 |
| `Olson` | `"208m"` | O8a / 57; O8b / 58 | D11, D12 |
| `Olson` | `"221m"` | O13a / 63; O13b / 64 | D17, D18 |
| `Olson` | `"218m"` | O15a / 66; O15b / 67 | D20, D21 |
| `Olson` | `"219m"` | O16 / 68; O21 / 73 | D22, D27 |
| `Fernandez-Pello` | `"215M"` | P3a / 77; P3b / 78 | D4, D5 |
| `Fernandez-Pello` | `"197m"` | P4 / 79; P8 / 82 | D6, D9 |
| `Fernandez-Pello` | `"202m"` | P5 / 80; P9 / 83 | D7, D10 |
| `Fernandez-Pello` | `"203m"` | P13a / 86; P13b / 87 | D13, D14 |
| `Fernandez-Pello` | `"196M"` | P21a / 95; P21b / 96 | D22, D23 |
| `Fernandez-Pello` | `"200m"` | P22a / 97; P22b / 98 | D24, D25 |
| `T'ien` | `"182m"` | T3 / 104; T7 / 108 | D4, D8 |
| `T'ien` | `"144m"` | T20 / 120; T28a / 128; T28b / 129 | D20, D28, D29 |
| `T'ien` | `"145m"` | T21 / 121; T29 / 130 | D21, D30 |
| `T'ien` | `"146m"` | T22 / 122; T27 / 127 | D22, D27 |
| `T'ien` | `"133m"` | T23 / 123; T24 / 124 | D23, D24 |
