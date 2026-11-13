# Curator's review: PanScan (dbGaP phs000206)

*A review of the public documentation of a real NCI study in dbGaP, written to understand how a large, multi-site cancer consortium is structured for controlled-access sharing. Only public pages were used; no controlled-access data were requested or viewed. Reviewed November 2026.*

## The study in brief

| Item | What the public record shows |
| --- | --- |
| Full title | Whole Genome Scan for Pancreatic Cancer Risk in the Pancreatic Cancer Cohort Consortium and Pancreatic Cancer Case-Control Consortium (PanScan) |
| Current version | phs000206.v7.p3 (seven versions, v1.p1 to v7.p3) |
| Funding | National Cancer Institute (contract HHSN261200800001E and grant K07 CA140790), with foundation support |
| Principal investigators | Laufey Amundadottir (NCI), Brian Wolpin (Dana-Farber), Rachael Stolzenberg-Solomon (NCI) |
| Design | Genome-wide association study; case-control design drawing on longitudinal cohorts |
| Contributing studies | 12 prospective cohorts and 8 case-control studies in PanScan I and II; 14 cohorts in PanScan III (9 returning, 5 new) |
| Consented subjects | 11,247 on the v7.p3 page; genotype and phenotype data cover 9,437 individuals |

Source: [dbGaP study page, phs000206.v7.p3](https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs000206.v7.p3).

## What a curator notices

### 1. One study, many consent groups

PanScan pools participants from about twenty studies, each with its own consent forms. That produces several consent groups rather than one. Public records show at least two:

- **DS-PACA-GSO**: disease-specific (pancreatic cancer), genetic studies only
- **DS-PACA-IRB-COL-GSO**: the same, plus local IRB approval and collaboration with the study PI

The second group's extra modifiers most likely reflect the terms of particular contributing sites' consent forms. For a curator, this is the core risk in consortium data: every subject must be coded to the group matching the form they actually signed, and the site-by-site table in the Institutional Certification is what that coding is checked against.

### 2. Consent travels all the way to the sample record

Each submitted sample gets a public BioSample record. One PanScan record, [SAMN00475570](https://www.ebi.ac.uk/biosamples/samples/SAMN00475570), shows the fields a curator's files ultimately feed:

| BioSample field | Value | Comes from |
| --- | --- | --- |
| gap_accession | phs000206 | Study registration |
| gap_consent_code | 2 | `CONSENT` in the Subject Consent file |
| gap_consent_short_name | DS-PACA-GSO | Consent group defined by the GPA from the Institutional Certification |
| body site | Peripheral Blood | `BODY_SITE` in Sample Attributes |
| biospecimen repository | NCI_PanScan | Sample submission metadata |
| title | "Non-tumor DNA sample from Peripheral Blood of a human male participant…" | Appears to be generated from `IS_TUMOR`, `ANALYTE_TYPE`, `BODY_SITE` and `SEX` |

This is why Sample Attributes and Subject Consent errors matter beyond dbGaP itself: a wrong `IS_TUMOR` or `SEX` value becomes a wrong public description of a sample.

### 3. Versioning in practice

The consented-subject count grows across versions while the participant set stays at p3: 7,747 on the v4.p3 page, 9,437 on v6.p3, and 11,247 on v7.p3. PanScan III added 1,582 new European-ancestry cases (and 173 Asian-ancestry cases from the Shanghai Men's and Women's Health Study), so subjects were clearly added over time.

**Open question I'd ask the team:** NCBI's documentation ties the participant-set number to changes in subjects or consents, so how does dbGaP decide when an addition increments `p` and when it doesn't? The difference between "consented subjects" and "individuals with data" (11,247 vs. 9,437) is part of the answer, but I'd want to understand the rule before updating a study myself.

### 4. Data that live elsewhere

PanScan's summary statistics cover 13,962 European-ancestry subjects (5,117 cases and 8,845 controls), more than the 9,437 individuals with posted genotypes. The difference is controls borrowed from other GWAS, whose raw data stay under the study where they were originally genotyped rather than being duplicated. A curator handling an update has to know which subjects belong to this accession and which are only referenced.

### 5. Old data dictionaries were XML

Early PanScan releases used XML data dictionaries, e.g. `phs000206.v1.pht000896.v1.CGEMS_PANSCAN_Subject.data_dict_2009_09_28.xml`. Current submissions use .xlsx or tab-delimited dictionaries, which dbGaP converts on release. An update to a legacy study may mean reconciling a modern dictionary with a 2009-era one.

### 6. The pages themselves are changing

The study page notes that classic dbGaP study pages will be discontinued on March 31, 2027, in favor of modernized pages, alongside the new dbGaP Registration System released in beta in July 2026.

## Takeaways for my own curation practice

1. In consortium studies, check consent coding **site by site**, not just study-wide.
2. Treat Sample Attributes and SEX as public-facing: they end up in BioSample records.
3. Keep a version log that separates "subjects added", "consents changed" and "data corrected", so every `v` and `p` increment can be explained.
4. Before updating a legacy study, compare old and new data dictionaries variable by variable.

## Sources

- [dbGaP study page: phs000206.v7.p3](https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs000206.v7.p3)
- [dbGaP study page: phs000206.v6.p3](https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs000206.v6.p3)
- [dbGaP study page: phs000206.v4.p3](https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs000206.v4.p3)
- [BioSample SAMN00475570 (EMBL-EBI mirror)](https://www.ebi.ac.uk/biosamples/samples/SAMN00475570)
- [OmicsDI record for phs000206](https://www.omicsdi.org/dataset/dbgap/phs000206) (legacy file names)
- [Law Insider excerpt of the PanScan study page](https://Www.lawinsider.com/clause/submitting-investigator) (consent group DS-PACA-IRB-COL-GSO)
- [dbGaP Study Submission Guide](https://www.ncbi.nlm.nih.gov/gap/docs/submissionguide/)
