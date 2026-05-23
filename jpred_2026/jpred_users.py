#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click",
#     "jinja2",
# ]
# ///
"""
Generate individual user prediction pages and users index for JPred 2026.

Scoring (per prediction):
  - 2 points for exact position match
  - 1 point for being in the correct zone (top 3 or bottom 3 of each group)
  Maximum 3 points per prediction.

Winner predictions (j1_winner, j2_3_winner) are playoff-determined and
shown without scoring until the playoff results are available.

Usage:
    jpred_users.py [--year YEAR]
"""
import re
import click
import sys
import sqlite3
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from pathlib import Path


def team_id(name):
    """Convert a team name to a URL-safe anchor ID."""
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


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
    cursor.execute("SELECT Name FROM jpred")
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
group_labels  = _load_labels("labels/group_labels.tsv")

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

# Scoring config per group:
#   table    - DB table key (combined with year: "{table}_{year}")
#   positions - expected position for each prediction in the group
#   zones     - (low, high) bonus zone for each prediction
#               a point is awarded if the actual position falls in this range
GROUP_SCORING = {
    "j1_east": {
        "table":     "j1_east",
        "positions": [1, 2, 3, 8, 9, 10],
        "zones":     [(1, 3), (1, 3), (1, 3), (8, 10), (8, 10), (8, 10)],
    },
    "j1_west": {
        "table":     "j1_west",
        "positions": [1, 2, 3, 8, 9, 10],
        "zones":     [(1, 3), (1, 3), (1, 3), (8, 10), (8, 10), (8, 10)],
    },
    "j2_3_east_a": {
        "table":     "j2_3_east_a",
        "positions": [1, 10],
        "zones":     [(1, 3), (8, 10)],
    },
    "j2_3_east_b": {
        "table":     "j2_3_east_b",
        "positions": [1, 10],
        "zones":     [(1, 3), (8, 10)],
    },
    "j2_3_west_a": {
        "table":     "j2_3_west_a",
        "positions": [1, 10],
        "zones":     [(1, 3), (8, 10)],
    },
    "j2_3_west_b": {
        "table":     "j2_3_west_b",
        "positions": [1, 10],
        "zones":     [(1, 3), (8, 10)],
    },
    # winner predictions are playoff-determined: no table to look up yet
    "j1_winner":   None,
    "j2_3_winner": None,
}


def get_team_position(conn, table_name, team_name):
    """Return a team's position from the league table, or None if not found."""
    try:
        cursor = conn.cursor()
        cursor.execute(f'SELECT Position FROM "{table_name}" WHERE Team = ?', (team_name,))
        row = cursor.fetchone()
        return row[0] if row else None
    except sqlite3.OperationalError:
        return None


def score_prediction(actual_pos, expected_pos, zone):
    """Return points for one prediction: 2 for exact match + 1 for correct zone.

    Only call when actual_pos is not None.
    """
    low, high = zone
    points = 0
    if actual_pos == expected_pos:
        points += 2
    if low <= actual_pos <= high:
        points += 1
    return points


def write_one_user(conn, name, html_filename, env, year="2026"):
    template = env.get_template('templates/user_template.html')

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jpred WHERE Name = ?", (name,))
    row = cursor.fetchone()
    if row is None:
        print(f"No data for {name}, skipping.")
        return

    predictions = {}
    total_score = 0
    j1_exact = 0
    j2j3_exact = 0
    j1_score = 0
    j2j3_score = 0
    has_any_score = False

    J1_GROUPS    = {"j1_east", "j1_west"}
    J2J3_GROUPS  = {"j2_3_east_a", "j2_3_east_b", "j2_3_west_a", "j2_3_west_b"}

    for group, cols in league_predictions.items():
        if not cols:
            continue

        scoring = GROUP_SCORING.get(group)
        group_preds = []

        for i, col in enumerate(cols):
            team = row[col] if col in row.keys() else ""
            position = "-"
            score = "-"

            if scoring and team:
                table_name = f"{scoring['table']}_{year}"
                actual_pos = get_team_position(conn, table_name, team)
                if actual_pos is not None:
                    position = actual_pos
                    pts = score_prediction(actual_pos, scoring["positions"][i], scoring["zones"][i])
                    score = pts
                    total_score += pts
                    has_any_score = True
                    if group in J1_GROUPS:
                        j1_score += pts
                        if pts >= 2:
                            j1_exact += 1
                    elif group in J2J3_GROUPS:
                        j2j3_score += pts
                        if pts >= 2:
                            j2j3_exact += 1

            group_preds.append({
                "Prediction": column_labels.get(col, col),
                "Team":       team,
                "Position":   position,
                "Score":      score,
            })

        predictions[group] = group_preds

    rendered_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    display_total = total_score if has_any_score else "-"
    with open(html_filename, "w") as html_file:
        html_content = template.render(
            predictions=predictions,
            name=name,
            total_score=display_total,
            year=year,
            group_labels=group_labels,
            rendered_at=rendered_at,
        )
        html_file.write(html_content)
    print(f"Written {html_filename}")
    if not has_any_score:
        return None
    return {
        "total":       total_score,
        "j1_exact":    j1_exact,
        "j2j3_exact":  j2j3_exact,
        "total_exact": j1_exact + j2j3_exact,
        "j1":          j1_score,
        "j2j3":        j2j3_score,
    }


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
    env.filters['team_id'] = team_id

    conn = create_connection(db_path)
    names = get_all_users(conn)

    scores = {}
    for name in names:
        if '/' in name:
            print(f"Skipping {name} (contains /)")
            continue
        html_filename = f"docs/preds/{name}.html"
        score = write_one_user(conn, name, html_filename, env, year)
        scores[name] = score

    conn.close()

    # Sort: total desc, total_exact desc, j1_exact desc
    scored = sorted(
        [(s, n) for n, s in scores.items() if s is not None],
        key=lambda x: (-x[0]["total"], -x[0]["total_exact"], -x[0]["j1_exact"])
    )
    unscored = sorted(n for n, s in scores.items() if s is None)
    ordered_leaderboard = (
        [(s["total"], n, s) for s, n in scored] +
        [("-", n, {}) for n in unscored]
    )

    rendered_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    leaderboard_data = dict(ordered_leaderboard=ordered_leaderboard, year=year, rendered_at=rendered_at)

    template = env.get_template('templates/users.html')
    with open('docs/users.html', 'w') as f:
        f.write(template.render(**leaderboard_data))
    print("Written docs/users.html")

    template = env.get_template('templates/index.html')
    with open('docs/index.html', 'w') as f:
        f.write(template.render(**leaderboard_data))
    print("Written docs/index.html")


if __name__ == '__main__':
    main()  # type: ignore[call-arg]
