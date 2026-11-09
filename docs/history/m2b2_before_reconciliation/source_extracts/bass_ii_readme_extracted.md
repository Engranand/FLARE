# BASS-II readme extracted — acquisition blocked

Checked 2026-11-05T12:00:46.810348+00:00. Status: **pending_manual_download**; content inspection **not_performed**. This is an acquisition-status record, not a substitute NASA document or a successful extraction.

## Source identity and observation

NASA PSI-25, BASS-II, DOI `10.60555/4qc4-de67`, [official investigation page](https://psi.nasa.gov/physci/repo/data/investigations/PSI-25), Version 4. Science Documents lists `PSI-25_Science Documents_BASS-II_ReadMe.docx`, displayed size **21.03 KB**, date added **Tue Nov 25 2025**. The displayed size is not a verified byte count. Actual filename, size in bytes, SHA-256, retrieval time and download URL are null because bytes were not acquired. No placeholder original was created.

## Acquisition evidence

The ReadMe was selected and Download clicked. The download listener returned `Timed out after 20000ms waiting for download.` The workbook was then selected alone and Download attempted with a 20000 ms listener; the browser operation ultimately returned `js execution timed out; kernel reset, rerun your request` (tool-reported duration 249.405 seconds). No local download path or original document bytes were returned. The ReadMe file-tree anchor had no href. No actual download URL was captured. A page console TypeError about an undefined length was observed, but its causal relationship to the download failures is unknown. These are failures of this acquisition attempt, not evidence that NASA has removed or corrupted the documents.

## Inspection limits

No text was extracted. Section headings, page/paragraph references, objectives, procedures, setup, fuel descriptions, instruments, airflow, calibration, gas measurement, radiometer settings, GMT, units, abbreviations and missing-value conventions cannot be verified without the DOCX bytes. No section structure or excerpts have been reconstructed.

## Required manual action

Open [NASA PSI-25](https://psi.nasa.gov/physci/repo/data/investigations/PSI-25), expand **Data files and documents → Science Documents** using the folder icon, select only the required filename, then click **Download**. Save the original bytes under `data/raw/bass_ii/original/` with the listed filename. Repeat for the other document. Do not re-save through Word or Excel. Subsequent verification must record the actual download URL, byte size, SHA-256 and retrieval time, then check the OOXML package and inspect its content.
