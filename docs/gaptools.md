# Running NCBI GaPTools on this submission

[GaPTools](https://github.com/ncbi/gaptools) is NCBI's pre-submission validator for dbGaP. It runs in Docker, checks the Subject Consent, Subject-Sample Mapping, Sample Attributes and Pedigree files against each other (and against PLINK or VCF genotype files when present), and shows results in a browser dashboard.

## Steps

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Clone GaPTools:
   ```bash
   git clone https://github.com/ncbi/gaptools && cd gaptools
   ```
3. Copy this repository's `submission/` folder into `gaptools/input_files/MockNCI/`.
4. Create `input_files/MockNCI/metadata.json`, the manifest that lists each file and its type. Use the example manifest in the GaPTools repository as the template; the file types here are subject consent, subject-sample mapping, sample attributes, pedigree, and phenotype, each with its data dictionary.
5. Run:
   ```bash
   ./dbgap-docker.bash -i ./input_files/MockNCI/ -o ./output_files/MockNCI -m ./input_files/MockNCI/metadata.json up
   ```
6. Open `http://localhost:8080` to view the report.

## GaPTools vs. the scripts in this repository

GaPTools' documented focus is consistency between the subject consent, sample mapping, sample attributes and pedigree files, and between those files and genotype data. The scripts here overlap with that, and add checks that are curator judgment calls rather than file-format rules:

- phenotype dictionary vs. dataset: exact VARNAMEs, undefined codes, ranges, undocumented missing codes
- HIPAA Safe Harbor scans: full dates, ZIP codes, ages over 89, names in free text
- encoding problems: Windows line endings, non-ASCII characters, hidden whitespace in IDs
- sample logic: tumor-labelled samples not marked as tumor

Running both, and comparing what each one flags, is a good exercise in itself.

For phenotype dictionaries, the CRAN package [dbGaPCheckup](https://CRAN.R-project.org/package=dbGaPCheckup) adds deeper dictionary checks.
