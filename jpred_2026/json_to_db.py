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

Supports both the 2026 regional format (j1_east, j1_west, j2_3_east_a, etc.)
and the legacy format (j1, j2, j3). Auto-detects which format is present based
on which JSON files exist in the year directory.

Japanese club names from the scraper are translated to English using
jp_name_mapping.csv so that league table Team names match prediction names.

Usage:
    json_to_db.py [YEAR]

The script creates tables named {league}_{YEAR} in jpred_{YEAR}.db
"""

import json
import pandas as pd
import sqlite3
import sys
import click
from pathlib import Path

# 2026 regional competition groups
NEW_FORMAT_LEAGUES = [
    "j1_east", "j1_west",
    "j2_3_east_a", "j2_3_east_b",
    "j2_3_west_a", "j2_3_west_b",
]

# Legacy single-table format
OLD_FORMAT_LEAGUES = ["j1", "j2", "j3"]


def load_jp_mapping(csv_path):
    """Load Japanese→English team name mapping from jp_name_mapping.csv."""
    p = Path(csv_path)
    if not p.exists():
        return {}
    df = pd.read_csv(p)
    return dict(zip(df['Japanese'], df['English']))


def json_to_db(json_path, db_path, table_name, jp_mapping):
    """Import a single JSON standings file into an SQLite table."""
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    records = []
    for entry in data:
        japanese_name = entry['Club']
        english_name = jp_mapping.get(japanese_name, japanese_name)
        records.append({
            'Team':     english_name,
            'Position': entry['Position'],
        })

    df = pd.DataFrame(records)
    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()
    print(f"Imported {len(records)} teams from {json_path} into {table_name}")


@click.command()
@click.argument('year', required=False)
def main(year):
    """Convert JSON league standings to SQLite database.

    YEAR: Season year (e.g. 2026). Auto-detects from tables/ if omitted.
    """
    if not year:
        tables_dir = Path('tables')
        year_dirs = [d for d in tables_dir.iterdir() if d.is_dir() and d.name.isdigit()]
        if not year_dirs:
            print("Error: No year directory found in tables/")
            sys.exit(1)
        year = year_dirs[0].name

    year_path = Path('tables') / year
    db_path = f'jpred_{year}.db'
    jp_mapping = load_jp_mapping('jp_name_mapping.csv')

    # Detect format from which JSON files exist
    new_files = [year_path / f"{league}.json" for league in NEW_FORMAT_LEAGUES]
    old_files = [year_path / f"{league}.json" for league in OLD_FORMAT_LEAGUES]

    if any(f.exists() for f in new_files):
        leagues = NEW_FORMAT_LEAGUES
    else:
        leagues = OLD_FORMAT_LEAGUES

    for league in leagues:
        json_file = year_path / f"{league}.json"
        if json_file.exists():
            json_to_db(json_file, db_path, f"{league}_{year}", jp_mapping)
        else:
            print(f"Skipping {json_file} (not found)")

    print(f"\nDatabase {db_path} updated.")


if __name__ == '__main__':
    main()
