-- dbGaP pre-submission QC in SQL (SQLite syntax; the joins work the same in PostgreSQL/Oracle).
-- Load:  sqlite3 qc.db < load_sqlite.sql   then   sqlite3 -header -column qc.db < qc_checks.sql

-- 1. THE classic question: every phenotype subject must have a consent record.
--    LEFT JOIN + IS NULL is the anti-join pattern.
SELECT '1 PHE subject with no consent record' AS chk, p.SUBJECT_ID
FROM phe p LEFT JOIN sc s ON TRIM(p.SUBJECT_ID) = s.SUBJECT_ID
WHERE s.SUBJECT_ID IS NULL;

-- Same thing with NOT EXISTS (often faster on big tables)
SELECT '1b NOT EXISTS version' AS chk, p.SUBJECT_ID
FROM phe p
WHERE NOT EXISTS (SELECT 1 FROM sc s WHERE s.SUBJECT_ID = TRIM(p.SUBJECT_ID));

-- 2. Consent-0 subjects that leaked into phenotype or sample files
SELECT '2 CONSENT=0 in PHE' AS chk, s.SUBJECT_ID
FROM sc s JOIN phe p ON TRIM(p.SUBJECT_ID) = s.SUBJECT_ID
WHERE s.CONSENT = '0';

SELECT '2b CONSENT=0 with samples' AS chk, m.SUBJECT_ID, m.SAMPLE_ID
FROM ssm m JOIN sc s ON s.SUBJECT_ID = m.SUBJECT_ID
WHERE s.CONSENT = '0';

-- 3. Duplicated primary keys
SELECT '3 duplicate SC SUBJECT_ID' AS chk, SUBJECT_ID, COUNT(*) AS n, GROUP_CONCAT(CONSENT) AS consents
FROM sc GROUP BY SUBJECT_ID HAVING COUNT(*) > 1;

SELECT '3b sample mapped to >1 subject' AS chk, SAMPLE_ID, COUNT(DISTINCT SUBJECT_ID) AS n_subjects
FROM ssm GROUP BY SAMPLE_ID HAVING COUNT(DISTINCT SUBJECT_ID) > 1;

-- 4. Consent codes not defined in the dictionary
SELECT '4 undefined consent code' AS chk, CONSENT, COUNT(*) AS n
FROM sc WHERE CONSENT NOT IN (SELECT code FROM consent_codes) AND CONSENT <> '0'
GROUP BY CONSENT;

-- 5. Subject count per consent group (compare with the IC and the PI's enrollment numbers)
SELECT '5 subjects per consent' AS chk, CONSENT, COUNT(DISTINCT SUBJECT_ID) AS n_subjects
FROM sc GROUP BY CONSENT ORDER BY CONSENT;

-- 6. SSM <-> SA both directions (a FULL OUTER JOIN written as two anti-joins for SQLite)
SELECT '6 in SSM not SA' AS chk, m.SAMPLE_ID FROM ssm m LEFT JOIN sa a ON a.SAMPLE_ID = m.SAMPLE_ID WHERE a.SAMPLE_ID IS NULL
UNION ALL
SELECT '6 in SA not SSM', a.SAMPLE_ID FROM sa a LEFT JOIN ssm m ON m.SAMPLE_ID = a.SAMPLE_ID WHERE m.SAMPLE_ID IS NULL;

-- 7. Pedigree: father must be male, mother female (self-join to SC twice)
SELECT '7 parent sex wrong' AS chk, p.SUBJECT_ID, p.FATHER, f.SEX AS father_sex, p.MOTHER, mo.SEX AS mother_sex
FROM ped p
LEFT JOIN sc f  ON f.SUBJECT_ID  = p.FATHER
LEFT JOIN sc mo ON mo.SUBJECT_ID = p.MOTHER
WHERE f.SEX = '2' OR mo.SEX = '1';

-- 8. Out-of-range and HIPAA-sensitive values (CAST, CASE)
SELECT '8 AGE_DX check' AS chk, SUBJECT_ID, AGE_DX,
       CASE WHEN CAST(AGE_DX AS INTEGER) IN (-9, 999) THEN 'undocumented missing code'
            WHEN CAST(AGE_DX AS INTEGER) > 89 THEN 'age > 89: top-code as 90+'
            ELSE 'out of range' END AS issue
FROM phe
WHERE CAST(AGE_DX AS INTEGER) < 18 OR CAST(AGE_DX AS INTEGER) > 89;

SELECT '8b full date' AS chk, SUBJECT_ID, YEAR_DX FROM phe WHERE YEAR_DX LIKE '____-__-__';
