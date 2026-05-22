#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click",
#     "icecream",
#     "jinja2",
# ]
# ///
"""
Generate individual user prediction pages and users index for JPred.

This module creates HTML pages for each participant showing their predictions across
all leagues, along with calculated scores based on actual results from
league table JSON files. It also generates a users index page listing all participants.

The scoring system awards points based on prediction accuracy:
- J1: 2 points for exact position match (top 3 or bottom 3), 1 point for correct group
- J2/J3: 2 points for exact position match (top 6 or bottom 3), 1 point for correct group

Leaderboard is sorted by: total points, then exact matches, then J1 score, J2 score, J3 score.
Results are saved to a 'results' table in the database with rankings.

Usage:
    jpred_users.py

The script auto-detects the year from the tables/ directory structure and generates
pages in the docs/preds/ directory.
"""
import click
import sys
import sqlite3
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from pathlib import Path


# Function to connect to the SQLite database
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as e:
        print(e)
    return conn


def get_all_users(conn):
    cursor = conn.cursor()
    cursor.execute(f'''SELECT Name FROM jpred''')
    # return as a list strings
    return [row["Name"] for row in cursor.fetchall()]

def _load_cols(path):
    return [line.strip() for line in Path(path).read_text().splitlines() if line.strip()]

def _load_labels(path):
    labels = {}
    for line in Path(path).read_text().splitlines()[1:]:  # skip header
        if '\t' in line:
            col, label = line.split('\t', 1)
            labels[col.strip()] = label.strip()
    return labels

column_labels = _load_labels("labels/column_labels.tsv")
group_labels = _load_labels("labels/group_labels.tsv")

league_predictions = {
    "j1_winner":   _load_cols("cols/j1_winner.cols"),
    "j1_east":     _load_cols("cols/j1_east.cols"),
    "j1_west":     _load_cols("cols/j1_west.cols"),
    "j2_3_winner": _load_cols("cols/j2_3_winner.cols"),
    "j2_3_east_a": _load_cols("cols/j2_3_east_a.cols"),
    "j2_3_east_b": _load_cols("cols/j2_3_east_b.cols"),
    "j2_3_west_a": _load_cols("cols/j2_3_west_a.cols"),
    "j2_3_west_b": _load_cols("cols/j2_3_west_b.cols"),
}

def j1_score(index):
    if index < 4:
        return f"""CASE
          WHEN position = {index} THEN 1 ELSE 0 END
          + CASE WHEN position IN (1, 2, 3) THEN 1 ELSE 0
            END"""
    else:
        return f"""CASE
          WHEN position = {index+11} THEN 1 ELSE 0 END
          + CASE WHEN position IN (8, 9, 10 ) THEN 1 ELSE 0
            END"""

def j2_j3_score(index):
    if index < 7:
        return f"""CASE
          WHEN position = {index} THEN 1 ELSE 0 END
          + CASE WHEN position IN (1, 2, 3, 4, 5, 6) THEN 1 ELSE 0
            END"""
    else:
        return f"""CASE
          WHEN position = {index+11} THEN 1 ELSE 0 END
          + CASE WHEN position IN (8, 9, 10 ) THEN 1 ELSE 0
            END"""


score_criteria={ 
                "j1": j1_score,
                "j2": j2_j3_score
        }


def make_league_score_SQL(name,league,year):
    table=f"{league}_{year}"
    sql_unions=[]

    for index, prediction_name in enumerate(league_predictions[league],start=1):
        #nic(index, prediction_name)

        ONE_PREDICTION_SQL=f"""
        SELECT {index} as "Index", Position, Prediction, Team, Position, 
            {score_criteria[league](index)} Score FROM
            (
            SELECT *, (SELECT Position FROM {table} WHERE {table}.Team = prediction.Team) AS Position 
            FROM (SELECT
                    Name,
                    {index} AS "Order",
                    '{prediction_name.title()}' as Prediction ,
                    [{prediction_name}] AS Team
                FROM jpred
                WHERE Name = '{name}'
            ) as prediction )"""

        sql_unions.append(ONE_PREDICTION_SQL)


    #ic(sql_unions)
    return " UNION ".join(sql_unions)

def query_database(conn, sql):
    cursor = conn.cursor()
    cursor.execute(sql)
    return cursor



def write_one_user(conn, name, html_filename, env, year="2026"):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('templates/user_template.html')

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jpred WHERE Name = ?", (name,))
    row = cursor.fetchone()
    if row is None:
        print(f"No data for {name}, skipping.")
        return

    predictions = {}
    for group, cols in league_predictions.items():
        if not cols:
            continue
        predictions[group] = [
            {"Prediction": column_labels.get(col, col), "Team": row[col] if col in row.keys() else "", "Position": "-", "Score": "-"}
            for col in cols
        ]

    rendered_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(html_filename, "w") as html_file:
        html_content = template.render(predictions=predictions, name=name, total_score="-", year=year, group_labels=group_labels, rendered_at=rendered_at)
        html_file.write(html_content)
    print(f"Written {html_filename}")

def _main():
    print(make_league_score_SQL("Stuart Woodward","j3","2024"))

@click.command()
@click.option('--year', default=None, help='Year to generate (e.g. 2026). Auto-detects from tables/ if omitted.')
def main(year):
    if not year:
        tables_dir = Path('tables')
        if tables_dir.exists():
            year_dirs = [d for d in tables_dir.iterdir() if d.is_dir() and d.name.isdigit()]
            year = year_dirs[0].name if year_dirs else None
        if not year:
            print("Error: could not detect year. Use --year.")
            sys.exit(1)

    db_path = f'jpred_{year}.db'
    preds_dir = Path('docs/preds')
    for f in preds_dir.glob('*.html'):
        f.unlink()
    preds_dir.mkdir(parents=True, exist_ok=True)
    env = Environment(loader=FileSystemLoader('.'))

    conn = create_connection(db_path)
    names = get_all_users(conn)
    for name in names:
        if '/' in name:
            print(f"Skipping {name} (contains /)")
            continue
        html_filename = f"docs/preds/{name}.html"
        write_one_user(conn, name, html_filename, env, year)

    conn.close()

    ordered_leaderboard = [
        ("-", name, {"total_exact_matches": "-", "j1": "-", "j2": "-", "j3": "-"})
        for name in names if '/' not in name
    ]
    template = env.get_template('templates/users.html')
    with open('docs/users.html', 'w') as f:
        f.write(template.render(ordered_leaderboard=ordered_leaderboard, year=year))
    print("Written docs/users.html")

if __name__ == '__main__':
    main()

