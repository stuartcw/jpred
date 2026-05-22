#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas",
#     "click",
# ]
# ///

import pandas as pd
import click
from pathlib import Path

@click.command()
@click.option('--sort-by', '-s', type=click.Choice(['time', 'name', 'email']), default='time',
              help='Sort by: time (default), name, or email')
@click.option('--reverse', '-r', is_flag=True, help='Reverse sort order')
@click.argument('year', required=False)
def main(sort_by, reverse, year):
    """Check submission times from JPred form responses CSV.

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

    if not Path(csv_file_path).exists():
        print(f"Error: CSV file '{csv_file_path}' not found")
        exit(1)

    # Read the CSV file
    df = pd.read_csv(csv_file_path)

    # Get the relevant columns
    # Column names might vary, so we'll try to find them
    timestamp_col = None
    name_col = None
    email_col = None

    for col in df.columns:
        if 'timestamp' in col.lower():
            timestamp_col = col
        elif 'name' in col.lower() and 'nickname' in col.lower():
            name_col = col
        elif 'email' in col.lower():
            email_col = col

    if not all([timestamp_col, name_col, email_col]):
        print("Error: Could not find required columns in CSV")
        print(f"Found columns: {list(df.columns)}")
        exit(1)

    # Extract relevant data
    submissions = df[[timestamp_col, name_col, email_col]].copy()
    submissions.columns = ['Timestamp', 'Name', 'Email']

    # Parse timestamp
    submissions['Timestamp'] = pd.to_datetime(submissions['Timestamp'], format='%d/%m/%Y %H:%M:%S', errors='coerce')

    # Sort based on user choice
    sort_column = {
        'time': 'Timestamp',
        'name': 'Name',
        'email': 'Email'
    }[sort_by]

    submissions = submissions.sort_values(sort_column, ascending=not reverse)

    # Print header
    print(f"\nSubmissions for JPred {year}")
    print(f"Total submissions: {len(submissions)}")
    print(f"Sorted by: {sort_by} ({'descending' if reverse else 'ascending'})")
    print("\n" + "="*100)
    print(f"{'Timestamp':<22} {'Name':<30} {'Email':<40}")
    print("="*100)

    # Print submissions
    for idx, row in submissions.iterrows():
        timestamp = row['Timestamp'].strftime('%Y-%m-%d %H:%M:%S') if pd.notna(row['Timestamp']) else 'N/A'
        name = str(row['Name'])[:29] if pd.notna(row['Name']) else 'N/A'
        email = str(row['Email'])[:39] if pd.notna(row['Email']) else 'N/A'
        print(f"{timestamp:<22} {name:<30} {email:<40}")

    # Print duplicate submissions summary
    print("\n" + "="*100)
    duplicate_emails = submissions[submissions.duplicated(subset='Email', keep=False)]
    if len(duplicate_emails) > 0:
        print(f"\nDuplicate submissions (same email): {len(duplicate_emails)}")
        print("\nEmails with multiple submissions:")
        for email in duplicate_emails['Email'].unique():
            dupes = submissions[submissions['Email'] == email].sort_values('Timestamp')
            print(f"\n  {email}:")
            for idx, row in dupes.iterrows():
                timestamp = row['Timestamp'].strftime('%Y-%m-%d %H:%M:%S') if pd.notna(row['Timestamp']) else 'N/A'
                print(f"    {timestamp} - {row['Name']}")
    else:
        print("\nNo duplicate submissions found")

    # Print duplicate names summary
    duplicate_names = submissions[submissions.duplicated(subset='Name', keep=False)]
    if len(duplicate_names) > 0:
        print(f"\nDuplicate names (different emails): {len(duplicate_names)}")
        print("\nNames with multiple entries:")
        for name in duplicate_names['Name'].unique():
            dupes = submissions[submissions['Name'] == name].sort_values('Timestamp')
            print(f"\n  {name}:")
            for idx, row in dupes.iterrows():
                print(f"    {row['Email']}")
    else:
        print("\nNo duplicate names found")

if __name__ == "__main__":
    main()
