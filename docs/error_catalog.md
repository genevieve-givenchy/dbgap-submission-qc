# Error catalog: the 24 planted problems and how each is resolved

Severity: **BLOCK** = dbGaP will reject or stop processing · **PRIVACY** = HIPAA / de-identification issue, must fix before anything leaves the institution · **ASK PI** = needs the study team's source records; never guess.

## Formatting

| # | File | Where | Problem | Severity | Fix |
|---|---|---|---|---|---|
| 1 | SA_DS | whole file | Windows CRLF line endings (`\r\n`) | BLOCK | `sed -i 's/\r$//'` or `dos2unix`; it also leaves `\r` glued to the last column in naive parsers |
| 2 | SA_DS | SM-0016-T | Non-ASCII character in "carcinóma" | BLOCK | Replace with ASCII ("carcinoma"); check the source system's export encoding |
| 3 | PHE_DS | S0033 | Trailing space in SUBJECT_ID ("S0033 ") so it doesn't match SC | BLOCK | Trim whitespace; ask how the export was produced (Excel copy-paste is the usual cause) |

## Uniqueness and consent

| # | File | Where | Problem | Severity | Fix |
|---|---|---|---|---|---|
| 4 | SC_DS | S0012 | Subject listed twice, once CONSENT=1 and once CONSENT=2 | BLOCK + ASK PI | One subject = one consent group. Ask the PI which consent form S0012 signed; keep only that row |
| 5 | SC_DS | S0027 | CONSENT=3, but SC_DD and the IC define only 1 (GRU) and 2 (HMB-IRB) | BLOCK + ASK PI | Either a typo, or a third site/consent group missing from the IC. The GPA must confirm; never invent a group |
| 6 | PHE_DS | S0005 | CONSENT=0 subject has phenotype data | BLOCK | Remove S0005 from PHE. CONSENT=0 is only for pedigree linking and public controls |
| 7 | SSM/SA | SM-0005-N | CONSENT=0 subject has a sample | BLOCK | Remove the sample from SSM, SA and the molecular files, or get the consent corrected if S0005 actually consented |
| 8 | SSM_DS | SM-0020-N | One sample mapped to two subjects (S0020 and S0021) | BLOCK + ASK PI | Likely a sample swap or copy-paste error. Lab must confirm; GRAF would also flag it |

## Cross-file IDs

| # | File | Where | Problem | Severity | Fix |
|---|---|---|---|---|---|
| 9 | PHE_DS | S0099 | Subject has phenotypes but no consent record | BLOCK + ASK PI | Get the consent record, or remove the subject |
| 10 | SSM_DS | S0098 | Subject in SSM but not in SC | BLOCK + ASK PI | Same as above |
| 11 | SSM/SA | SM-0031-T | Sample in SSM but missing from SA | BLOCK | Get BODY_SITE, ANALYTE_TYPE, IS_TUMOR for it |
| 12 | SA_DS | SM-0099-N | Sample in SA but not in SSM: no subject | BLOCK | Find its subject or drop it |

## Pedigree

| # | File | Where | Problem | Severity | Fix |
|---|---|---|---|---|---|
| 13 | PED_DS | S0043 | FATHER (S0042) is female and MOTHER (S0041) is male: columns swapped | BLOCK | Swap FATHER/MOTHER for S0043; confirm with family records |
| 14 | PED_DS | S0051 | MOTHER S0077 doesn't exist in SC | BLOCK | Add S0077 to SC (CONSENT=0 if she didn't consent) or set MOTHER to 0 |
| 15 | PED vs SC | S0052 | SEX=1 in PED, SEX=2 in SC | BLOCK + ASK PI | One is wrong. Genotype-inferred sex (GRAF) settles it |

## Sample attributes

| # | File | Where | Problem | Severity | Fix |
|---|---|---|---|---|---|
| 16 | SA_DS | SM-0010-T | "-T" (tumor) sample has IS_TUMOR=No | ASK PI | Either the label or the attribute is wrong; ask the biorepository |

## Dictionary vs data

| # | File | Where | Problem | Severity | Fix |
|---|---|---|---|---|---|
| 17 | PHE_DD | Smoking_Status | VARNAME case doesn't match DS header SMOKING_STATUS | BLOCK | VARNAMEs must match exactly: fix the DD |
| 18 | PHE_DS | SMOKING_STATUS, S0030 | Value 4 has no code in VALUES (0, 1, 2 only) | BLOCK + ASK PI | Ask what 4 means; add the code or correct the value |
| 19 | PHE_DS | AGE_DX, S0008 (-9) and S0014 (999) | Missing-value codes not documented in DD and outside MIN/MAX | BLOCK | Add `-9=Missing` (pick one code), recode 999 to it, and document in VALUES. Missing codes are not MIN/MAX |
| 20 | PHE_DS | BMI, S0025 | BMI = 250, outside the logical range | ASK PI | Probably a unit or entry error (25.0?). Never "fix" silently |
| 21 | PHE_DS | ZIP | Column not in the DD at all | BLOCK | Remove it (see #23) |

## Privacy (HIPAA Safe Harbor)

| # | File | Where | Problem | Severity | Fix |
|---|---|---|---|---|---|
| 22 | PHE_DS | YEAR_DX, S0035 | Full date 2019-03-14 | PRIVACY | Keep the year only (2019) or convert to days from an anchor event |
| 23 | PHE_DS | ZIP, S0018 and S0044 | 5-digit ZIP codes | PRIVACY | Drop the column. Safe Harbor allows at most the first 3 digits, and only where that area has more than 20,000 people |
| 24 | PHE_DS | AGE_DX, S0022 | Age 93 | PRIVACY | Top-code ages over 89 into one category ("90+") and say so in the DD |
| 24b | PHE_DS | NOTES, S0046 | Free text contains a name ("Pt Jane Doe") | PRIVACY | Redact. dbGaP's scripts don't catch names; humans do. Ask whether NOTES needs to be shared at all |

(#24b is a bonus: free-text fields are where identifiers hide.)

## What a good curation log entry looks like

> **PHE_DS.txt, S0022, AGE_DX = 93.** Ages over 89 are an identifier under HIPAA Safe Harbor. Proposed fix: recode all AGE_DX > 89 to 90 and add "90 = 90 years or older" to the DD (1 subject affected). No PI input needed unless the study's IRB protocol says otherwise.

> **SC_DS.txt, S0027, CONSENT = 3.** The IC and SC_DD define consent groups 1 (GRU) and 2 (HMB-IRB) only. Question for PI/GPA: is S0027 from a site whose consent form isn't covered by the current IC? Submission is on hold for this subject until resolved.
