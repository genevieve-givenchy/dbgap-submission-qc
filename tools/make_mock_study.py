"""Generate a mock dbGaP submission (NCI-style breast cancer cohort) with planted errors.
All data are synthetic. Output: ../submission/ (regenerates the practice files)
"""
import os, random
random.seed(20261113)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "submission")
os.makedirs(OUT, exist_ok=True)

def write(name, header, rows, crlf=False):
    nl = "\r\n" if crlf else "\n"
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(header) + nl)
        for r in rows:
            f.write("\t".join("" if v is None else str(v) for v in r) + nl)

def write_dd(name, rows):
    # dbGaP prefers .xlsx DDs; tab-delimited .txt is used here so every tool can read it.
    # VALUES must be the last column; extra codes spill into unnamed columns to the right.
    maxv = max(len(r[-1]) for r in rows)
    header = ["VARNAME", "VARDESC", "TYPE", "UNITS", "MIN", "MAX", "VALUES"] + [""] * (maxv - 1)
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(header) + "\n")
        for r in rows:
            vals = r[-1] + [""] * (maxv - len(r[-1]))
            f.write("\t".join(str(x) for x in list(r[:-1]) + vals) + "\n")

# ---------------- Subjects ----------------
subjects = [f"S{n:04d}" for n in range(1, 61)]          # S0001..S0060
sex = {s: 2 for s in subjects}                           # breast cancer cohort: mostly female
for s in ["S0007", "S0019", "S0041", "S0050"]:
    sex[s] = 1
consent = {s: random.choice([1, 1, 1, 2]) for s in subjects}
consent["S0005"] = 0          # unconsented pedigree-linking relative
consent["S0040"] = 0          # unconsented father, links pedigree
sex["S0040"] = 1
consent["S0027"] = 3          # ERROR: consent code 3 not defined in DD

sc_rows = [[s, consent[s], sex[s]] for s in subjects]
sc_rows.insert(13, ["S0012", 2, 2])   # ERROR: duplicate SUBJECT_ID with conflicting consent
write("SC_DS.txt", ["SUBJECT_ID", "CONSENT", "SEX"], sc_rows)
write_dd("SC_DD.txt", [
    ["SUBJECT_ID", "De-identified subject ID", "string", "", "", "", []],
    ["CONSENT", "Consent group as determined by the IRB-approved consent forms", "encoded", "", "", "",
     ["1=General Research Use (GRU)", "2=Health/Medical/Biomedical (IRB) (HMB-IRB)"]],
    ["SEX", "Biological sex", "encoded", "", "", "", ["1=Male", "2=Female"]],
])

# ---------------- Subject-Sample Mapping ----------------
ssm = []
for s in subjects:
    if s in ("S0040",):                       # consent-0 father: no samples (correct)
        continue
    n = int(s[1:])
    ssm.append([s, f"SM-{n:04d}-N"])
    if sex[s] == 2 and consent[s] != 0:
        ssm.append([s, f"SM-{n:04d}-T"])
ssm.append(["S0021", "SM-0020-N"])            # ERROR: SAMPLE_ID already mapped to S0020
ssm.append(["S0098", "SM-0098-N"])            # ERROR: subject not in SC
write("SSM_DS.txt", ["SUBJECT_ID", "SAMPLE_ID"], ssm)
write_dd("SSM_DD.txt", [
    ["SUBJECT_ID", "De-identified subject ID", "string", "", "", "", []],
    ["SAMPLE_ID", "De-identified sample ID", "string", "", "", "", []],
])

# ---------------- Sample Attributes ----------------
sa = []
seen = set()
for subj, samp in ssm:
    if samp in seen or samp == "SM-0031-T":   # ERROR: SM-0031-T is in SSM but missing from SA
        continue
    seen.add(samp)
    tumor = samp.endswith("-T")
    sa.append([samp, "Breast" if tumor else "Blood", "DNA", "Yes" if tumor else "No",
               "Invasive ductal carcinoma" if tumor else ""])
for r in sa:
    if r[0] == "SM-0010-T":
        r[3] = "No"                            # ERROR: tumor sample marked IS_TUMOR=No
    if r[0] == "SM-0016-T":
        r[4] = "Invasive lobular carcinóma"  # ERROR: non-ASCII character
sa.append(["SM-0099-N", "Blood", "DNA", "No", ""])  # ERROR: in SA, not in SSM
write("SA_DS.txt", ["SAMPLE_ID", "BODY_SITE", "ANALYTE_TYPE", "IS_TUMOR", "HISTOLOGICAL_TYPE"],
      sa, crlf=True)                           # ERROR: Windows CRLF line endings
write_dd("SA_DD.txt", [
    ["SAMPLE_ID", "De-identified sample ID", "string", "", "", "", []],
    ["BODY_SITE", "Body site where sample was collected", "string", "", "", "", []],
    ["ANALYTE_TYPE", "Analyte type", "string", "", "", "", []],
    ["IS_TUMOR", "Tumor status", "encoded", "", "", "", ["Yes=Tumor", "No=Normal"]],
    ["HISTOLOGICAL_TYPE", "Histological type of tumor", "string", "", "", "", []],
])
# Note: S0005 (CONSENT=0) has sample SM-0005-N in SSM and SA -> ERROR (consent-0 with sample)

# ---------------- Pedigree ----------------
ped = [
    ["F01", "S0040", 0, 0, 1],
    ["F01", "S0003", 0, 0, 2],
    ["F01", "S0004", "S0040", "S0003", 2],
    ["F01", "S0005", "S0040", "S0003", 2],
    ["F02", "S0041", 0, 0, 1],                 # S0041 is male in SC
    ["F02", "S0042", 0, 0, 2],
    ["F02", "S0043", "S0042", "S0041", 2],    # ERROR: FATHER/MOTHER swapped (father is female)
    ["F03", "S0050", 0, 0, 1],
    ["F03", "S0051", "S0050", "S0077", 2],    # ERROR: MOTHER S0077 not in SC
    ["F03", "S0052", "S0050", 0, 1],          # ERROR: SEX=1 here but SEX=2 in SC
]
write("PED_DS.txt", ["FAMILY_ID", "SUBJECT_ID", "FATHER", "MOTHER", "SEX"], ped)
write_dd("PED_DD.txt", [
    ["FAMILY_ID", "Family ID", "string", "", "", "", []],
    ["SUBJECT_ID", "De-identified subject ID", "string", "", "", "", []],
    ["FATHER", "Father's SUBJECT_ID; 0 = not in study", "string", "", "", "", []],
    ["MOTHER", "Mother's SUBJECT_ID; 0 = not in study", "string", "", "", "", []],
    ["SEX", "Biological sex", "encoded", "", "", "", ["1=Male", "2=Female"]],
])

# ---------------- Phenotypes ----------------
phe = []
for s in subjects:
    if s == "S0040":
        continue                               # correct: consent-0 father excluded
    age = random.randint(32, 78)
    bmi = round(random.uniform(19, 38), 1)
    smk = random.choice([0, 1, 2])
    er = random.choice(["Positive", "Negative"])
    yr = random.randint(2008, 2021)
    phe.append([s, age, bmi, smk, er, yr, "", ""])
# planted errors
def setp(subj, col, val):
    idx = {"AGE_DX": 1, "BMI": 2, "SMOKING_STATUS": 3, "ER_STATUS": 4, "YEAR_DX": 5,
           "ZIP": 6, "NOTES": 7}[col]
    for r in phe:
        if r[0] == subj:
            r[idx] = val
setp("S0008", "AGE_DX", -9)                  # missing code (OK if documented; DD doesn't document it)
setp("S0014", "AGE_DX", 999)                 # missing code, undocumented
setp("S0022", "AGE_DX", 93)                  # ERROR: HIPAA age > 89
setp("S0025", "BMI", 250)                    # ERROR: out of range
setp("S0030", "SMOKING_STATUS", 4)           # ERROR: code not defined in DD
setp("S0035", "YEAR_DX", "2019-03-14")       # ERROR: full date (HIPAA)
setp("S0018", "ZIP", "20892")                # ERROR: ZIP column (HIPAA + not in DD)
setp("S0044", "ZIP", "20814")
setp("S0046", "NOTES", "Pt Jane Doe refused second biopsy")  # ERROR: name in free text
for r in phe:
    if r[0] == "S0033":
        r[0] = "S0033 "                        # ERROR: trailing whitespace in ID
phe.append(["S0099", 51, 27.4, 1, "Negative", 2016, "", ""])   # ERROR: subject not in SC
write("PHE_DS.txt", ["SUBJECT_ID", "AGE_DX", "BMI", "SMOKING_STATUS", "ER_STATUS", "YEAR_DX", "ZIP", "NOTES"], phe)
write_dd("PHE_DD.txt", [
    ["SUBJECT_ID", "De-identified subject ID", "string", "", "", "", []],
    ["AGE_DX", "Age at breast cancer diagnosis", "integer", "years", 18, 89, []],
    ["BMI", "Body mass index at enrollment", "decimal", "kg/m2", 12, 70, []],
    ["Smoking_Status", "Smoking status at enrollment", "encoded", "", "", "",
     ["0=Never", "1=Former", "2=Current"]],                     # ERROR: VARNAME case mismatch
    ["ER_STATUS", "Estrogen receptor status of primary tumor", "string", "", "", "", []],
    ["YEAR_DX", "Calendar year of diagnosis", "integer", "year", 2000, 2025, []],
    ["NOTES", "Clinical coordinator notes", "string", "", "", "", []],
])
print("wrote", sorted(os.listdir(OUT)))
