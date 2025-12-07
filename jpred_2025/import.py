#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas",
#     "click",
# ]
# ///
"""
Import JPred predictions from CSV to SQLite database.

This module reads JPred form responses from a CSV file and imports them into an SQLite
database. It performs several data processing steps:
- Normalizes column names to match the expected schema
- Maps team names from form responses to standardized table names
- Removes duplicate submissions (keeping only the latest per email)
- Obfuscates email addresses for privacy
- Makes duplicate participant names unique by appending obfuscated emails

Usage:
    import.py [YEAR]

Example:
    import.py 2025
    import.py  # auto-detects year from tables/ directory
"""

import pandas as pd
import sqlite3
import click
from pathlib import Path
from email_tools import obfuscate_email

def csv_to_sqlite(csv_file_path, sqlite_db_path, table_name):
    """
    Reads a CSV file into a pandas DataFrame and inserts it into an SQLite database.

    Parameters:
    - csv_file_path: The file path of the CSV file.
    - sqlite_db_path: The file path of the SQLite database.
    - table_name: The name of the table where the CSV data will be inserted.
    """
    # Read the CSV file
    df = pd.read_csv(csv_file_path)

    # Normalize column names to match expected schema
    column_mapping = {
        'Name or Nickname': 'Name',
        'Contact Email Address (Not Published)': 'Email'
    }

    # Also normalize prediction column names - remove prefixes
    for col in df.columns:
        if col.startswith('J1 Predictions [') or col.startswith('J2 Predictions [') or col.startswith('J3 Predictions ['):
            # Extract the part inside brackets
            new_name = col[col.find('[') + 1:col.find(']')]
            column_mapping[col] = new_name
        elif col.startswith(' [J'):
            # Handle columns that start with space like " [J2 First Place]"
            new_name = col[col.find('[') + 1:col.find(']')]
            column_mapping[col] = new_name

    df.rename(columns=column_mapping, inplace=True)

    # Normalize team names to match JSON table names
    team_mapping_file = Path('team_name_mapping.csv')
    if team_mapping_file.exists():
        team_mapping_df = pd.read_csv(team_mapping_file)
        team_mapping = dict(zip(team_mapping_df['FormName'], team_mapping_df['TableName']))

        # Apply mapping to all prediction columns (any column with "Place" in the name)
        prediction_columns = [col for col in df.columns if 'Place' in col]

        for col in prediction_columns:
            if col in df.columns:
                df[col] = df[col].map(lambda x: team_mapping.get(x, x) if pd.notna(x) else x)

        mapped_count = len(team_mapping)
        print(f"Applied {mapped_count} team name mappings")

    # Remove duplicate submissions - keep only the latest submission per email
    if 'Email' in df.columns and 'Timestamp' in df.columns:
        original_count = len(df)
        # Sort by Timestamp to ensure latest is kept
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        df = df.sort_values('Timestamp')
        # Keep last (latest) submission per email
        df = df.drop_duplicates(subset='Email', keep='last')
        removed_count = original_count - len(df)
        if removed_count > 0:
            print(f"Removed {removed_count} duplicate submission(s), keeping latest per email")

    # Obfuscate all email addresses in the database
    if 'Email' in df.columns:
        df['Email'] = df['Email'].apply(obfuscate_email)
        print("Obfuscated all email addresses")

    # Make duplicate names unique by appending obfuscated email
    if 'Name' in df.columns and 'Email' in df.columns:
        # Find duplicate names
        name_counts = df['Name'].value_counts()
        duplicate_names = name_counts[name_counts > 1].index.tolist()

        if duplicate_names:
            for dup_name in duplicate_names:
                # For each duplicate name, append obfuscated email to ALL instances
                mask = df['Name'] == dup_name
                emails = df.loc[mask, 'Email'].values
                for row_idx, email in zip(df[mask].index, emails):
                    df.loc[row_idx, 'Name'] = f"{dup_name} ({email})"
            print(f"Made {len(duplicate_names)} duplicate name(s) unique")

    # Connect to the SQLite database
    conn = sqlite3.connect(sqlite_db_path)

    # Write the data to a SQLite table
    df.to_sql(table_name, conn, if_exists='replace', index=False)

    # Close the database connection
    conn.close()
    print(f"Data from {csv_file_path} has been inserted into {table_name} table in {sqlite_db_path} database.")

@click.command()
@click.argument('year', required=False)
def main(year):
    """Import JPred CSV data into SQLite database.

    YEAR: The year to process (e.g., 2025). If not provided, auto-detects from tables/ directory.
    """
    if not year:
        # Auto-detect year from tables directory structure
        tables_dir = Path('tables')
        year_dirs = [d for d in tables_dir.iterdir() if d.is_dir() and d.name.isdigit()]

        if not year_dirs:
            print("Error: No year directory found in tables/")
            exit(1)

        year = year_dirs[0].name

    csv_file_path = f'JPred {year} - Form responses 1.csv'
    sqlite_db_path = f'jpred_{year}.db'
    table_name = 'jpred'

    csv_to_sqlite(csv_file_path, sqlite_db_path, table_name)

if __name__ == "__main__":
    main()

