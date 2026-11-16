#!/usr/bin/env python3
"""dbGaP pre-submission QC in pandas.
Usage:  python qc_checks.py ../submission
Each check prints PASS or the offending rows. Read top to bottom: it follows the order
a curator would work in (formatting -> IDs -> consent -> cross-file -> dictionary -> privacy).
"""
import re, sys
from pathlib import Path
import pandas as pd

D = Path(sys.argv[1] if len(sys.argv) > 1 else "../submission")
problems = 0

def report(title, bad):
    """bad = list or DataFrame of offending items; empty = pass."""
    global problems
    n = len(bad)
    print(f"\n[{'PASS' if n == 0 else 'FAIL'}] {title}" + ("" if n == 0 else f"  ({n})"))
    if n:
        problems += 1
        print(bad.to_string(index=False) if isinstance(bad, pd.DataFrame) else "  " + ", ".join(map(str, bad)))

# ---------- 0. Raw-file checks (before pandas hides them) ----------
for f in sorted(D.glob("*_DS.txt")):
    raw = f.read_bytes()
    if b"\r\n" in raw:
        report(f"{f.name}: Windows CRLF line endings", [f.name])
    bad_chars = sorted({ch for ch in raw.decode("utf-8") if ord(ch) > 127})
    if bad_chars:
        report(f"{f.name}: non-ASCII characters", bad_chars)

# Load everything as text (dtype=str) so IDs like 007 or 1e5 are never reinterpreted.
def load(name):
    return pd.read_csv(D / name, sep="\t", dtype=str, keep_default_na=False)

sc, ssm, sa, ped, phe = (load(f"{x}_DS.txt") for x in ["SC", "SSM", "SA", "PED", "PHE"])
sa.columns = sa.columns.str.strip()          # CRLF leaves '\r' on the last header

# ---------- 1. ID formatting ----------
id_ok = re.compile(r"^[A-Za-z0-9._\-@#]+$")   # dbGaP-allowed characters, no spaces
for name, df, col in [("SC", sc, "SUBJECT_ID"), ("SSM", ssm, "SUBJECT_ID"), ("SSM", ssm, "SAMPLE_ID"),
                      ("SA", sa, "SAMPLE_ID"), ("PED", ped, "SUBJECT_ID"), ("PHE", phe, "SUBJECT_ID")]:
    bad = df[~df[col].str.match(id_ok)][[col]]
    report(f"{name}.{col}: illegal characters or whitespace", bad.assign(**{col: bad[col].map(repr)}))

# Strip whitespace for the remaining checks so one bad space doesn't cascade into ten failures.
for df in (sc, ssm, sa, ped, phe):
    for c in df.columns:
        df[c] = df[c].str.strip()

# ---------- 2. Uniqueness of primary keys ----------
report("SC: duplicate SUBJECT_ID", sc[sc.duplicated("SUBJECT_ID", keep=False)])
report("SSM: duplicate SAMPLE_ID (one sample, two subjects)", ssm[ssm.duplicated("SAMPLE_ID", keep=False)])
report("SA: duplicate SAMPLE_ID", sa[sa.duplicated("SAMPLE_ID", keep=False)])
report("PHE: duplicate SUBJECT_ID", phe[phe.duplicated("SUBJECT_ID", keep=False)])

# ---------- 3. Consent ----------
sc_dd = pd.read_csv(D / "SC_DD.txt", sep="\t", dtype=str, keep_default_na=False)
cons_row = sc_dd[sc_dd.VARNAME == "CONSENT"].iloc[0]
defined = {v.split("=")[0] for v in cons_row.iloc[6:] if "=" in v} | {"0"}   # 0 is implicit
report("SC: CONSENT codes not defined in SC_DD", sorted(set(sc.CONSENT) - defined))

consent0 = set(sc.loc[sc.CONSENT == "0", "SUBJECT_ID"])
report("PHE: CONSENT=0 subjects present (must be removed)", sorted(consent0 & set(phe.SUBJECT_ID)))
c0_samples = ssm[ssm.SUBJECT_ID.isin(consent0)]
report("SSM/SA: samples belonging to CONSENT=0 subjects", c0_samples)

print("\nSubjects per consent group:\n" + sc.drop_duplicates("SUBJECT_ID").CONSENT.value_counts().sort_index().to_string())

# ---------- 4. Cross-file ID consistency ----------
sc_ids = set(sc.SUBJECT_ID)
report("PHE subjects missing from SC", sorted(set(phe.SUBJECT_ID) - sc_ids))
report("SSM subjects missing from SC", sorted(set(ssm.SUBJECT_ID) - sc_ids))
report("SSM samples missing from SA", sorted(set(ssm.SAMPLE_ID) - set(sa.SAMPLE_ID)))
report("SA samples missing from SSM", sorted(set(sa.SAMPLE_ID) - set(ssm.SAMPLE_ID)))
# The same check written as an anti-join:
orphans = phe.merge(sc, on="SUBJECT_ID", how="left", indicator=True).query("_merge == 'left_only'")
assert set(orphans.SUBJECT_ID) == set(phe.SUBJECT_ID) - sc_ids

# ---------- 5. Pedigree ----------
parents = pd.concat([ped.FATHER, ped.MOTHER])
parents = set(parents[~parents.isin(["0", ""])])
report("PED: parent IDs missing from SC", sorted(parents - sc_ids))
report("PED: subjects missing from SC", sorted(set(ped.SUBJECT_ID) - sc_ids))
sex_of = dict(zip(sc.SUBJECT_ID, sc.SEX))
report("PED: FATHER is not male", ped[ped.FATHER.map(sex_of).eq("2")][["SUBJECT_ID", "FATHER"]])
report("PED: MOTHER is not female", ped[ped.MOTHER.map(sex_of).eq("1")][["SUBJECT_ID", "MOTHER"]])
m = ped.merge(sc, on="SUBJECT_ID", suffixes=("_PED", "_SC"))
report("PED vs SC: SEX disagrees", m[m.SEX_PED != m.SEX_SC][["SUBJECT_ID", "SEX_PED", "SEX_SC"]])

# ---------- 6. Sample attributes logic ----------
report("SA: '-T' sample not marked IS_TUMOR=Yes",
       sa[sa.SAMPLE_ID.str.endswith("-T") & (sa.IS_TUMOR != "Yes")][["SAMPLE_ID", "IS_TUMOR"]])

# ---------- 7. Data dictionary vs dataset ----------
dd = pd.read_csv(D / "PHE_DD.txt", sep="\t", dtype=str, keep_default_na=False)
report("PHE: DS columns with no exact DD VARNAME", sorted(set(phe.columns) - set(dd.VARNAME)))
report("PHE_DD: VARNAMEs with no DS column", sorted(set(dd.VARNAME) - set(phe.columns)))

for _, v in dd.iterrows():
    col = v.VARNAME if v.VARNAME in phe.columns else next(
        (c for c in phe.columns if c.upper() == v.VARNAME.upper()), None)   # tolerate case to keep checking
    if col is None:
        continue
    vals = phe[col][phe[col] != ""]
    if v.TYPE == "encoded":
        codes = {x.split("=")[0] for x in v.iloc[6:] if "=" in x}
        report(f"PHE.{col}: values not defined in DD", sorted(set(vals) - codes))
    if v.TYPE in ("integer", "decimal"):
        num = pd.to_numeric(vals, errors="coerce")
        report(f"PHE.{col}: non-numeric values", sorted(vals[num.isna()].unique()))
        if v.MIN and v.MAX:
            out = phe.loc[num.index[(num < float(v.MIN)) | (num > float(v.MAX))], ["SUBJECT_ID", col]]
            report(f"PHE.{col}: outside DD range {v.MIN}-{v.MAX} (missing codes must be documented)", out)

# ---------- 8. Privacy (HIPAA Safe Harbor) ----------
date_like = re.compile(r"^\d{4}-\d{2}-\d{2}$|^\d{1,2}/\d{1,2}/\d{2,4}$")
dated = [(c, phe[phe[c].str.match(date_like)][["SUBJECT_ID", c]]) for c in phe.columns]
report("PHE: columns holding full dates", [c for c, hits in dated if len(hits)])
for c, hits in dated:
    if len(hits):
        print(hits.to_string(index=False))
report("PHE: ZIP / geographic column present", [c for c in phe.columns if re.search(r"zip|postal|county|city", c, re.I)])
ages = pd.to_numeric(phe.AGE_DX, errors="coerce")
report("PHE.AGE_DX: ages over 89 (top-code to 90+)", phe.loc[(ages > 89) & (ages < 900), ["SUBJECT_ID", "AGE_DX"]])
free = [c for c, t in zip(dd.VARNAME, dd.TYPE) if t == "string" and c in phe.columns and c != "SUBJECT_ID"]
name_like = re.compile(r"\b(?:Mr|Mrs|Ms|Dr|Pt|Patient)\.?\s+[A-Z][a-z]+", re.I)
for c in free:
    report(f"PHE.{c}: free text that may contain names (review by eye)",
           phe[phe[c].str.contains(name_like)][["SUBJECT_ID", c]])

print(f"\n==== {problems} checks failed ====")
