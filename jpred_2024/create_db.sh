rm jpred.db
./import.py
sqlite-utils create-table jpred.db j1_2024 Wikipedia TEXT Team TEXT Position INTEGER
sqlite-utils insert jpred.db j1_2024 JPred\ 2024\ -\ J1\ Teams.csv --csv
sqlite-utils create-table jpred.db j2_2024 Wikipedia TEXT Team TEXT Position INTEGER
sqlite-utils insert jpred.db j2_2024 JPred\ 2024\ -\ J2\ Teams.csv --csv
sqlite-utils create-table jpred.db j3_2024 Wikipedia TEXT Team TEXT Position INTEGER
sqlite-utils insert jpred.db j3_2024 JPred\ 2024\ -\ J3\ Teams.csv --csv
