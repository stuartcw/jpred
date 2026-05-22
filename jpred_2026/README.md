# JPred 2026

Results and predictions pages for the JPred 2026 football prediction competition,
covering the J1, J2, and J3 leagues (MEIJI YASUDA 100 YEAR VISION LEAGUE).

Live site: https://jpred.football/

## Overview

Participants submit their predictions via a Google Form. This project imports those
predictions, combines them with scraped J-League standings, and generates:

- Per-user prediction pages (`docs/preds/*.html`)
- A participant index page (`docs/users.html`)
- Aggregated statistics pages (`docs/j1.html`, `docs/j2.html`, `docs/j3.html`)
- A leaderboard image (`docs/leaderboard.png`)

## Directory Structure

```
jpred_2026/
  build_preds.sh              Import TSV and generate per-user prediction pages
  make_all.sh                 Full build: DB, stats pages, preds, leaderboard, assets
  create_db.sh                Import TSV and JSON standings into SQLite
  import.py                   Import Google Form TSV responses into SQLite
  json_to_db.py               Import scraped league standings JSON into SQLite
  jpred.py                    Generate aggregated stats HTML pages
  jpred_users.py              Generate per-user prediction HTML pages
  generate_leaderboard_image.py  Generate leaderboard PNG
  check_submissions.py        Inspect and validate the submissions database
  cols/                       Column lists defining which predictions each page shows
  labels/                     TSV files mapping column names to display labels
  tables/                     League standings JSON (produced by scrape/)
  templates/                  Jinja2 HTML templates
  docs/                       Generated output (deployed to jpred.football)
  assets/                     Favicons and static assets
  scrape/                     Standalone scraper for J-League standings (see scrape/README.md)
```

## Prerequisites

1. **Google Form TSV export** - Download the form responses as TSV and place in the
   project root. The filename must contain the year (e.g. `*2026*.tsv`).

2. **League standings JSON** - Run the scraper to download current standings:
   ```
   cd scrape
   ./update_tables.sh
   ```
   This produces `tables/2026/j1.json`, `tables/2026/j2.json`, `tables/2026/j3.json`.

## Generating prediction pages

```
./build_preds.sh
```

This runs the three steps in sequence:

| Step | Script | Input | Output |
|------|--------|-------|--------|
| 1 | `import.py` | `*2026*.tsv` | `jpred` table in `jpred_2026.db` |
| 2 | `json_to_db.py` | `tables/2026/*.json` | `j1_2026`, `j2_2026`, `j3_2026` tables |
| 3 | `jpred_users.py` | `jpred_2026.db`, `cols/`, `labels/` | `docs/preds/*.html`, `docs/users.html` |

## Full build (stats pages + leaderboard)

```
./make_all.sh
```

Runs the full pipeline including aggregated stats pages and leaderboard image.

## Configuration files

### `cols/` - Column definitions

Each `.cols` file lists the prediction columns (one per line) used to build a
page section. File names correspond to league groups:

| File | Content |
|------|---------|
| `j1_winner.cols` | J1 overall winner prediction |
| `j1_east.cols` | J1 East group top/bottom predictions |
| `j1_west.cols` | J1 West group top/bottom predictions |
| `j2_3_winner.cols` | J2/J3 overall winner |
| `j2_3_east_a.cols` | J2/J3 East-A group top/bottom |
| `j2_3_east_b.cols` | J2/J3 East-B group top/bottom |
| `j2_3_west_a.cols` | J2/J3 West-A group top/bottom |
| `j2_3_west_b.cols` | J2/J3 West-A Group B top/bottom |
| `all_cols.txt` | All prediction columns combined |

### `labels/` - Display labels

| File | Content |
|------|---------|
| `column_labels.tsv` | Maps database column names to human-readable labels |
| `group_labels.tsv` | Maps group keys to section heading labels |

## Data flow

```
Google Form
    |
    v TSV export
*2026*.tsv --> import.py --> jpred table
                                 |
scrape/ --> tables/2026/*.json --> json_to_db.py --> j1_2026, j2_2026, j3_2026 tables
                                                         |
                                                   jpred_users.py
                                                         |
                                                   docs/preds/*.html
                                                   docs/users.html
```

## Scoring

Points are awarded based on how close each prediction is to the actual finishing position:

- **J1**: 2 points for exact match in top 3 or bottom 3; 1 point for correct group
- **J2/J3**: 2 points for exact match in top 6 or bottom 3; 1 point for correct group

The leaderboard ranks participants by total points, then exact matches, then
J1 score, J2 score, J3 score.

## Dependencies

Python dependencies are managed automatically by `uv` via inline script metadata
in each `.py` file. No `pip install` or virtual environment setup is needed.
Run any script directly:

```
./import.py
./jpred_users.py
```
