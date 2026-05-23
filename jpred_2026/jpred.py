#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click",
#     "jinja2",
#     "pandas",
# ]
# ///
"""
Generate an aggregate prediction summary HTML page for one group.

Queries the jpred table for prediction counts per team per position column,
then renders a template showing how many participants predicted each team.
If a league table exists for the group, teams are also ordered by current position
and the results are exported to aggregated_data/{group}.csv.

Usage:
    jpred.py docs/j1_east.html cols/j1_east.cols
"""
import re
import click
import sqlite3
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from pathlib import Path


def team_id(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)
    return conn


def query_database(conn, column):
    cur = conn.cursor()
    cur.execute(
        f'SELECT "{column}", COUNT(*) as count FROM jpred GROUP BY "{column}" ORDER BY count DESC'
    )
    return cur.fetchall()


def load_tsv_labels(path):
    labels = {}
    for line in Path(path).read_text().splitlines()[1:]:
        if '\t' in line:
            col, label = line.split('\t', 1)
            labels[col.strip()] = label.strip()
    return labels


@click.command()
@click.argument('html_filename')
@click.argument('columns_file')
@click.option('--year', default=None, help='Season year (e.g. 2026). Auto-detects latest from tables/ if omitted.')
def main(html_filename, columns_file, year):
    if not year:
        tables_dir = Path('tables')
        year_dirs = [d for d in tables_dir.iterdir() if d.is_dir() and d.name.isdigit()]
        if not year_dirs:
            print("Error: No year directory found in tables/")
            raise SystemExit(1)
        year = max(d.name for d in year_dirs)

    column_labels = load_tsv_labels('labels/column_labels.tsv')

    db_path = f'jpred_{year}.db'
    conn = create_connection(db_path)
    if conn is None:
        print('Error! Cannot connect to the database.')
        raise SystemExit(1)

    columns = [c for c in Path(columns_file).read_text().splitlines() if c.strip()]
    division = Path(html_filename).stem  # e.g. "j1_east"

    # Try to get team ordering from the league table (may not exist for winner groups)
    cur = conn.cursor()
    try:
        cur.execute(f'SELECT Team FROM "{division}_{year}" ORDER BY Position')
        all_teams = [row[0] for row in cur.fetchall()]
    except sqlite3.OperationalError:
        all_teams = []

    data = {}
    csv_data = {team: {} for team in all_teams}

    for column in columns:
        results = query_database(conn, column)
        label = column_labels.get(column, column)
        data[label] = results
        for team, count in results:
            if team in csv_data:
                csv_data[team][label] = count

    conn.close()

    if all_teams:
        aggregated_dir = Path('aggregated_data')
        aggregated_dir.mkdir(exist_ok=True)
        csv_filename = aggregated_dir / f'{division}.csv'
        df = pd.DataFrame.from_dict(csv_data, orient='index')
        df.index.name = 'Team'
        df = df.fillna(0).astype(int)
        df = df.reindex(all_teams)
        df.to_csv(csv_filename)
        print(f'CSV file {csv_filename} has been created.')

    env = Environment(loader=FileSystemLoader('.'))
    env.filters['team_id'] = team_id
    template = env.get_template('templates/template.html')
    html_content = template.render(data=data, year=year)

    with open(html_filename, 'w') as html_file:
        html_file.write(html_content)
    print(f'HTML file {html_filename} has been created.')


if __name__ == '__main__':
    main()
