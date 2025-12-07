#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas",
#     "click",
# ]
# ///
"""
Import J-League standings from JSON files into SQLite database.

This module reads league table data from JSON files (j1.json, j2.json, j3.json) 
and imports them into an SQLite database. It maps team names to their Wikipedia 
names using a mapping CSV file, creating tables with team names, positions, and 
Wikipedia references for each league.

Usage:
    json_to_db.py [YEAR]

Example:
    json_to_db.py 2025
    json_to_db.py  # auto-detects year from tables/ directory

The script creates tables named j1_YEAR, j2_YEAR, and j3_YEAR in jpred_YEAR.db
"""

import json
import pandas as pd
import sqlite3
import sys
import os
import click
from pathlib import Path

def load_wikipedia_mapping(csv_path):
    """Load Wikipedia name mapping from CSV."""
    df = pd.read_csv(csv_path)
    return dict(zip(df['Team'], df['Wikipedia']))

def json_to_db(json_path, db_path, table_name, wikipedia_mapping):
    """Convert JSON file to SQLite table with Wikipedia names."""

    with open(json_path, 'r') as f:
        data = json.load(f)

    records = []
    for entry in data:
        team = entry['Club']
        wikipedia = wikipedia_mapping.get(team, team)

        records.append({
            'Wikipedia': wikipedia,
            'Team': team,
            'Position': entry['Position']
        })

    df = pd.DataFrame(records)

    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()

    print(f"Imported {len(records)} teams from {json_path} into {table_name}")

@click.command()
@click.argument('year', required=False)
def main(year):
    """Convert JSON league tables to SQLite database.

    YEAR: The year to process (e.g., 2025). If not provided, auto-detects from tables/ directory.
    """
    if not year:
        # Auto-detect year from tables directory structure
        tables_dir = Path('tables')
        year_dirs = [d for d in tables_dir.iterdir() if d.is_dir() and d.name.isdigit()]

        if not year_dirs:
            print("Error: No year directory found in tables/")
            sys.exit(1)

        # Use the first (or only) year directory found
        year = year_dirs[0].name

    tables_dir = Path('tables')
    year_path = tables_dir / year

    db_path = f'jpred_{year}.db'

    wikipedia_mapping = load_wikipedia_mapping('wikipedia.csv')

    json_to_db(year_path / 'j1.json', db_path, f'j1_{year}', wikipedia_mapping)
    json_to_db(year_path / 'j2.json', db_path, f'j2_{year}', wikipedia_mapping)
    json_to_db(year_path / 'j3.json', db_path, f'j3_{year}', wikipedia_mapping)

    print(f"\nDatabase {db_path} created successfully with j1_{year}, j2_{year}, and j3_{year} tables")

if __name__ == '__main__':
    main()
