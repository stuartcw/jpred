#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click",
#     "jinja2",
# ]
# ///
"""
Generate an A-Z team report showing who picked each team and for what prediction.

For every team that appears in any prediction column, lists the participants who
selected that team along with the position they predicted. Teams with no predictions
are also listed. Output: docs/teams.html

Usage:
    jpred_teams.py [--year YEAR]
"""
import re
import click
import sqlite3
from collections import defaultdict
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from pathlib import Path


def team_id(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn


def load_cols(path):
    return [line.strip() for line in Path(path).read_text().splitlines() if line.strip()]


def load_tsv_labels(path):
    labels = {}
    for line in Path(path).read_text().splitlines()[1:]:
        if '\t' in line:
            col, label = line.split('\t', 1)
            labels[col.strip()] = label.strip()
    return labels


# All prediction columns across all groups, in display order
GROUPS = [
    "j1_winner",
    "j1_east",
    "j1_west",
    "j2_3_winner",
    "j2_3_east_a",
    "j2_3_east_b",
    "j2_3_west_a",
    "j2_3_west_b",
]


@click.command()
@click.option('--year', default=None, help='Season year (e.g. 2026). Auto-detects latest from tables/ if omitted.')
def main(year):
    if not year:
        tables_dir = Path('tables')
        year_dirs = [d for d in tables_dir.iterdir() if d.is_dir() and d.name.isdigit()]
        if not year_dirs:
            print("Error: could not detect year. Use --year.")
            raise SystemExit(1)
        year = max(d.name for d in year_dirs)

    column_labels = load_tsv_labels('labels/column_labels.tsv')

    # Collect all prediction columns from all group cols files
    all_cols = []
    for group in GROUPS:
        cols_file = Path(f'cols/{group}.cols')
        if cols_file.exists():
            all_cols.extend(load_cols(cols_file))

    conn = create_connection(f'jpred_{year}.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jpred")
    rows = cursor.fetchall()

    # Build: team -> {prediction_label -> [name, ...]}  (insertion order preserved)
    team_pickers = defaultdict(dict)
    all_teams_seen = set()

    for col in all_cols:
        label = column_labels.get(col, col)
        for row in rows:
            if col not in row.keys():
                continue
            team = row[col]
            if not team:
                continue
            name = row["Name"]
            all_teams_seen.add(team)
            team_pickers[team].setdefault(label, []).append(name)

    # Also include all teams from league tables so teams with no predictions appear
    for group in GROUPS:
        table_name = f"{group}_{year}"
        try:
            cursor.execute(f'SELECT Team FROM "{table_name}" ORDER BY Team')
            for (team,) in cursor.fetchall():
                all_teams_seen.add(team)
        except sqlite3.OperationalError:
            pass

    conn.close()

    # Sort teams A-Z, build ordered list
    teams = []
    for team in sorted(all_teams_seen, key=str.casefold):
        pickers = team_pickers.get(team, {})
        teams.append({"name": team, "pickers": pickers})

    rendered_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    env = Environment(loader=FileSystemLoader('.'))
    env.filters['team_id'] = team_id
    template = env.get_template('templates/teams.html')
    html = template.render(teams=teams, year=year, rendered_at=rendered_at)

    out = Path('docs/teams.html')
    out.write_text(html)
    print(f"Written {out} ({len(teams)} teams)")


if __name__ == '__main__':
    main()
