-- Load the tab-delimited submission files into SQLite (run from the solutions/ folder).
.mode tabs
.import ../submission/SC_DS.txt sc
.import ../submission/SSM_DS.txt ssm
.import ../submission/SA_DS.txt sa
.import ../submission/PED_DS.txt ped
.import ../submission/PHE_DS.txt phe
CREATE TABLE consent_codes (code TEXT, label TEXT);
INSERT INTO consent_codes VALUES ('1', 'GRU'), ('2', 'HMB-IRB');
