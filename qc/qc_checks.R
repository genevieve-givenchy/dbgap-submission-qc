#!/usr/bin/env Rscript
# dbGaP pre-submission QC in R (tidyverse: readr + dplyr + stringr-style base regex)
# Usage: Rscript qc_checks.R ../submission
suppressPackageStartupMessages({ library(readr); library(dplyr) })
args <- commandArgs(trailingOnly = TRUE)
d <- if (length(args)) args[1] else "../submission"

# Read every column as character so IDs are never coerced; trim_ws = FALSE so we can SEE bad spaces.
rd <- function(f) read_tsv(file.path(d, f), col_types = cols(.default = "c"),
                           na = character(), trim_ws = FALSE, progress = FALSE)
sc <- rd("SC_DS.txt"); ssm <- rd("SSM_DS.txt"); sa <- rd("SA_DS.txt")
ped <- rd("PED_DS.txt"); phe <- rd("PHE_DS.txt")

report <- function(title, bad) {
  n <- if (is.data.frame(bad)) nrow(bad) else length(bad)
  cat(sprintf("\n[%s] %s%s\n", if (n == 0) "PASS" else "FAIL", title, if (n) sprintf("  (%d)", n) else ""))
  if (n) print(bad)
}

# 1. Whitespace / illegal characters in IDs
report("PHE.SUBJECT_ID illegal characters",
       phe %>% filter(!grepl("^[A-Za-z0-9._@#-]+$", SUBJECT_ID)) %>% select(SUBJECT_ID))
sc  <- sc  %>% mutate(across(everything(), trimws))
phe <- phe %>% mutate(across(everything(), trimws))

# 2. Duplicates
report("SC duplicate SUBJECT_ID", sc %>% group_by(SUBJECT_ID) %>% filter(n() > 1))
report("SSM duplicate SAMPLE_ID", ssm %>% group_by(SAMPLE_ID) %>% filter(n() > 1))

# 3. Consent: phenotype subjects with no consent record, as an anti-join
report("PHE subjects with no consent record (anti_join)",
       phe %>% anti_join(sc, by = "SUBJECT_ID") %>% select(SUBJECT_ID))
c0 <- sc %>% filter(CONSENT == "0") %>% pull(SUBJECT_ID)
report("PHE subjects with CONSENT=0", phe %>% filter(SUBJECT_ID %in% c0) %>% select(SUBJECT_ID))
report("Samples from CONSENT=0 subjects", ssm %>% filter(SUBJECT_ID %in% c0))
cat("\nSubjects per consent group:\n"); print(sc %>% distinct(SUBJECT_ID, .keep_all = TRUE) %>% count(CONSENT))

# 4. Cross-file
report("SSM subjects not in SC", setdiff(ssm$SUBJECT_ID, sc$SUBJECT_ID))
report("SSM samples not in SA", setdiff(ssm$SAMPLE_ID, sa$SAMPLE_ID))
report("SA samples not in SSM", setdiff(sa$SAMPLE_ID, ssm$SAMPLE_ID))

# 5. Pedigree sex logic
ped_chk <- ped %>%
  left_join(sc %>% select(FATHER = SUBJECT_ID, father_sex = SEX), by = "FATHER") %>%
  left_join(sc %>% select(MOTHER = SUBJECT_ID, mother_sex = SEX), by = "MOTHER")
report("PED father not male", ped_chk %>% filter(father_sex == "2") %>% select(SUBJECT_ID, FATHER))
report("PED mother not female", ped_chk %>% filter(mother_sex == "1") %>% select(SUBJECT_ID, MOTHER))
report("PED parents not in SC", setdiff(setdiff(c(ped$FATHER, ped$MOTHER), c("0", "")), sc$SUBJECT_ID))

# 6. DD vs DS, ranges, codes
dd <- read_tsv(file.path(d, "PHE_DD.txt"), col_types = cols(.default = "c"), na = character(),
               name_repair = "unique_quiet", progress = FALSE)
report("PHE columns not in DD (exact match)", setdiff(names(phe), dd$VARNAME))
age <- suppressWarnings(as.numeric(phe$AGE_DX))
report("AGE_DX outside 18-89", phe %>% filter(age < 18 | age > 89) %>% select(SUBJECT_ID, AGE_DX))
report("SMOKING_STATUS codes not in DD", setdiff(unique(phe$SMOKING_STATUS[phe$SMOKING_STATUS != ""]), c("0", "1", "2")))

# 7. Privacy
report("Full dates in YEAR_DX", phe %>% filter(grepl("^\\d{4}-\\d{2}-\\d{2}$", YEAR_DX)) %>% select(SUBJECT_ID, YEAR_DX))
report("Ages over 89", phe %>% filter(age > 89 & age < 900) %>% select(SUBJECT_ID, AGE_DX))
report("Geographic columns", grep("zip|postal|county", names(phe), ignore.case = TRUE, value = TRUE))
