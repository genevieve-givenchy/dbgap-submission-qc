#!/usr/bin/env bash
# dbGaP QC with standard Unix tools: works on multi-GB files without loading them into memory.
# Usage: bash qc_checks.sh ../submission
D=${1:-../submission}
cd "$D" || exit 1

echo "== Quick look: rows, columns, header =="
for f in *_DS.txt; do
  printf '%-12s rows=%-5s cols=%s\n' "$f" "$(($(wc -l < "$f") - 1))" "$(head -1 "$f" | awk -F'\t' '{print NF}')"
done

echo; echo "== Ragged rows (field count differs from header) =="
awk -F'\t' 'FNR==1{n=NF} NF!=n{print FILENAME": line "FNR" has "NF" fields, header has "n}' *_DS.txt

echo; echo "== Windows line endings and non-ASCII bytes =="
grep -l $'\r' *_DS.txt
grep -nP '[^\x00-\x7F]' *_DS.txt

echo; echo "== Trailing/leading spaces in any field =="
grep -nP '(^|\t) | (\t|$)' *_DS.txt | cat -A | head

echo; echo "== Duplicate SUBJECT_ID in SC (cut + sort + uniq -d) =="
cut -f1 SC_DS.txt | tail -n +2 | sort | uniq -d

echo; echo "== Sample mapped to more than one subject =="
cut -f2 SSM_DS.txt | tail -n +2 | sort | uniq -d

echo; echo "== Subjects per consent group (uniq -c) =="
tail -n +2 SC_DS.txt | cut -f2 | sort | uniq -c

echo; echo "== PHE subjects with no consent record =="
# comm needs two sorted lists; -23 = lines only in the first file
comm -23 <(tail -n +2 PHE_DS.txt | cut -f1 | sed 's/ *$//' | sort -u) \
         <(tail -n +2 SC_DS.txt  | cut -f1 | sort -u)

echo; echo "== Same check with awk only (hash lookup: first file builds the set, second probes it) =="
awk -F'\t' 'NR==FNR {if (FNR>1) ok[$1]=1; next} FNR>1 {id=$1; gsub(/ /,"",id); if (!(id in ok)) print id}' SC_DS.txt PHE_DS.txt

echo; echo "== CONSENT=0 subjects that appear in PHE =="
awk -F'\t' 'NR==FNR {if ($2=="0") c0[$1]=1; next} FNR>1 && ($1 in c0) {print $1}' SC_DS.txt PHE_DS.txt

echo; echo "== SSM samples missing from SA, and SA samples missing from SSM =="
comm -3 <(tail -n +2 SSM_DS.txt | cut -f2 | sort -u) <(tail -n +2 SA_DS.txt | cut -f1 | tr -d '\r' | sort -u)

echo; echo "== AGE_DX (col 2) outside 18-89 =="
awk -F'\t' 'FNR>1 && ($2<18 || $2>89) {print $1, $2}' PHE_DS.txt

echo; echo "== Values that look like full dates =="
grep -nE '[0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4}' PHE_DS.txt

echo; echo "== Header vs dictionary VARNAMEs (case-sensitive diff) =="
diff <(head -1 PHE_DS.txt | tr '\t' '\n' | sort) <(tail -n +2 PHE_DD.txt | cut -f1 | sort)

echo; echo "== Fix CRLF in place (shown, not run) =="
echo "sed -i 's/\r\$//' SA_DS.txt     # or: dos2unix SA_DS.txt"
