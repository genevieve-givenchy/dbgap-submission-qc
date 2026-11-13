# dbGaP Submission QC: a mock NCI study and a four-language validation suite

A self-directed curation project by **Genevieve Givenchy, PhD**. I built a complete mock dbGaP submission for a synthetic NCI-style breast cancer cohort, planted 24 realistic submission errors in it, and wrote pre-submission QC that catches every one, in **Python (pandas), R (dplyr), SQL and Unix tools (awk, sort, uniq, comm)**.

All data are synthetic. No real participant information is used anywhere in this repository.

## Why this project

dbGaP shares genomic and phenotype data under controlled access, split by participant consent group. A submission fails, or worse, breaches consent, when subject and sample IDs don't reconcile across files, when a non-consented subject leaks into the phenotype data, when a data dictionary disagrees with its dataset, or when an identifier survives de-identification. This project rehearses the checks a curator runs before NCBI ever sees the files.

## What's in the submission

The files follow the structure in NCBI's [dbGaP Study Submission Guide](https://www.ncbi.nlm.nih.gov/gap/docs/submissionguide/). Each dataset (DS) comes with a data dictionary (DD).

| File | Contents | Key |
| --- | --- | --- |
| `SC_DS.txt` | Subject Consent: every subject, consent group, sex | SUBJECT_ID |
| `SSM_DS.txt` | Subject-Sample Mapping: tumor and matched-normal samples | SAMPLE_ID |
| `SA_DS.txt` | Sample Attributes: body site, analyte, tumor status, histology | SAMPLE_ID |
| `PED_DS.txt` | Pedigree: three families, including a consent-0 linking parent | SUBJECT_ID |
| `PHE_DS.txt` | Subject phenotypes: age at diagnosis, BMI, smoking, ER status, year of diagnosis | SUBJECT_ID |

Consent groups: `1 = General Research Use (GRU)`, `2 = Health/Medical/Biomedical, IRB required (HMB-IRB)`, and `0 = not consented` (pedigree linking only).

## What the QC checks

| Area | Checks |
| --- | --- |
| File format | Windows line endings, non-ASCII characters, ragged rows, whitespace and illegal characters in IDs |
| Keys | Duplicate subjects in SC, samples mapped to more than one subject |
| Consent | Codes not defined in the dictionary, consent-0 subjects in phenotype or sample files, subject counts per group |
| Cross-file IDs | Phenotype and SSM subjects missing from SC; SSM and SA samples that don't match each other |
| Pedigree | Parents missing from SC, fathers not male, mothers not female, sex disagreeing between PED and SC |
| Sample logic | Tumor-labelled samples not marked IS_TUMOR = Yes |
| Dictionary vs data | Exact VARNAME match, undefined codes, non-numeric values, values outside MIN/MAX, undocumented missing codes (-9, 999) |
| HIPAA Safe Harbor | Full dates, ZIP codes, ages over 89, names in free text |

Every planted error, why it matters and how it should be resolved (including which ones must go back to the PI rather than be fixed by the curator) is in [`docs/error_catalog.md`](docs/error_catalog.md).

## Run it

```bash
# Python (pandas)
python3 qc/qc_checks.py submission

# R (readr + dplyr)
Rscript qc/qc_checks.R submission

# SQL (SQLite)
cd qc && sqlite3 qc.db < load_sqlite.sql && sqlite3 -header -column qc.db < qc_checks.sql && cd ..

# Unix tools
bash qc/qc_checks.sh submission
```

Example: the classic consent check (every phenotype subject must have a consent record) in each language:

```python
set(phe.SUBJECT_ID.str.strip()) - set(sc.SUBJECT_ID)          # pandas
```
```r
phe %>% anti_join(sc, by = "SUBJECT_ID")                       # dplyr
```
```sql
SELECT p.SUBJECT_ID FROM phe p LEFT JOIN sc s ON s.SUBJECT_ID = TRIM(p.SUBJECT_ID)
WHERE s.SUBJECT_ID IS NULL;                                    -- SQL anti-join
```
```bash
comm -23 <(tail -n +2 PHE_DS.txt | cut -f1 | sort -u) <(tail -n +2 SC_DS.txt | cut -f1 | sort -u)
```

To regenerate the mock submission, or plant new errors to test the checks: `python3 tools/make_mock_study.py`.

## Also in this repository

- [`docs/panscan_review.md`](docs/panscan_review.md): a curator's review of the public documentation of a real NCI dbGaP study, PanScan (phs000206), covering how its consent groups, versions and sample records are structured.
- [`docs/gaptools.md`](docs/gaptools.md): how to run NCBI's own validator, GaPTools, on this submission, and which checks it covers versus the scripts here.

## Design choices

- **Everything is read as text.** IDs such as `007` or `1E5` must never be reinterpreted as numbers.
- **Flag, don't fix.** The scripts report problems; they never alter source files. Curation decisions belong in a log and, for consent or sample-identity questions, with the PI and the NIH Genomic Program Administrator.
- **Streaming first for big files.** The Unix version uses `awk` hash lookups and `comm`, which work on multi-gigabyte files without loading them into memory.

## License

MIT. See [LICENSE](LICENSE).
