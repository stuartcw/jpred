#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests",
#     "beautifulsoup4",
#     "click",
# ]
# ///
"""
Scrape J.League standings for the 2026 100-Year Vision regional competition.

The 2026 season uses a regional conference format. Two source pages each contain
multiple groups, identified by <h4 class="leftRedTit"> section headers.

Source pages:
  https://www.jleague.jp/standings/j1/    -> EAST, WEST
  https://www.jleague.jp/standings/j2j3/  -> EAST-Aグループ, EAST-Bグループ,
                                             WEST-Aグループ, WEST-Bグループ

Usage:
  ./scrape.py --league j1_east
  ./scrape.py --league j1_west
  ./scrape.py --league j2_3_east_a
  ./update_tables.sh   # scrape all six groups
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import json
import click

current_year = datetime.now().year

# Maps CLI league name -> (cache_key, source_url, section_header_substring)
LEAGUE_CONFIG = {
    "j1_east":     ("j1",   "https://www.jleague.jp/standings/j1/",    "EAST"),
    "j1_west":     ("j1",   "https://www.jleague.jp/standings/j1/",    "WEST"),
    "j2_3_east_a": ("j2j3", "https://www.jleague.jp/standings/j2j3/",  "EAST-A"),
    "j2_3_east_b": ("j2j3", "https://www.jleague.jp/standings/j2j3/",  "EAST-B"),
    "j2_3_west_a": ("j2j3", "https://www.jleague.jp/standings/j2j3/",  "WEST-A"),
    "j2_3_west_b": ("j2j3", "https://www.jleague.jp/standings/j2j3/",  "WEST-B"),
}

FORM_MAP = {"01": "W", "02": "D", "03": "L"}


def safe_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def fetch_page(url, cache_key, download_dir, year):
    """Download a page (or return cached HTML if fresh enough)."""
    html_file = os.path.join(download_dir, f"{cache_key}_{year}.html")
    meta_file = os.path.join(download_dir, f"{cache_key}_{year}_meta.json")

    use_cache = False

    if os.path.exists(html_file) and os.path.exists(meta_file):
        try:
            with open(meta_file) as f:
                meta = json.load(f)
            cached_time = datetime.fromisoformat(meta["timestamp"])
            if (datetime.now() - cached_time).total_seconds() < 86400:
                use_cache = True
            else:
                try:
                    resp = requests.head(url)
                    last_modified = resp.headers.get("Last-Modified")
                    if last_modified and last_modified == meta.get("last_modified"):
                        meta["timestamp"] = datetime.now().isoformat()
                        with open(meta_file, "w") as f:
                            json.dump(meta, f)
                        use_cache = True
                except requests.exceptions.RequestException as e:
                    print(f"Warning: could not check server headers ({e}), using cache.")
                    use_cache = True
        except (json.JSONDecodeError, KeyError):
            use_cache = False

    if use_cache:
        print(f"Using cached {html_file}")
        with open(html_file, encoding="utf-8") as f:
            return f.read()

    print(f"Downloading {url}")
    resp = requests.get(url)
    if resp.status_code != 200:
        print(f"Error: HTTP {resp.status_code} for {url}")
        return None
    html = resp.text
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html)
    meta = {"last_modified": resp.headers.get("Last-Modified"), "timestamp": datetime.now().isoformat()}
    with open(meta_file, "w") as f:
        json.dump(meta, f)
    return html


def parse_form(td):
    """Extract form string (e.g. 'WDLWW') from the last-5-matches cell."""
    result = []
    for img in td.find_all("img"):
        src = img.get("src", "")
        # src looks like /img/common/ico_match01.png
        key = src.rsplit("ico_match", 1)[-1].replace(".png", "")
        result.append(FORM_MAP.get(key, "?"))
    return "".join(result)


def parse_section(html, section_id):
    """Find the standings table for the named section and return a list of team dicts."""
    soup = BeautifulSoup(html, "html.parser")

    target_h4 = None
    for h4 in soup.find_all("h4", class_="leftRedTit"):
        if section_id in h4.get_text():
            target_h4 = h4
            break

    if not target_h4:
        print(f"Error: section '{section_id}' not found. Available h4 headers:")
        for h4 in soup.find_all("h4", class_="leftRedTit"):
            print(f"  {h4.get_text().strip()}")
        return None

    table = target_h4.find_next("table", class_="scoreTable01")
    if not table:
        print(f"Error: no table found after section header '{section_id}'")
        return None

    rows = []
    for tr in table.find("tbody").find_all("tr"):
        cols = tr.find_all("td")
        if len(cols) < 12:
            continue
        # col[0] = icon, col[1] = position, col[2] = club, col[3] = points,
        # col[4] = played, col[5] = won, col[6] = PK won, col[7] = PK lost,
        # col[8] = lost, col[9] = GF, col[10] = GA, col[11] = GD, col[12] = form
        span = cols[2].find("span", class_="embS")
        club = span.get_text().strip() if span else cols[2].get_text().strip()
        rows.append({
            "Position":        safe_int(cols[1].get_text().strip()),
            "Club":            club,
            "Points":          safe_int(cols[3].get_text().strip()),
            "Played":          safe_int(cols[4].get_text().strip()),
            "Won":             safe_int(cols[5].get_text().strip()),
            "PK Won":          safe_int(cols[6].get_text().strip()),
            "PK Lost":         safe_int(cols[7].get_text().strip()),
            "Lost":            safe_int(cols[8].get_text().strip()),
            "Goals For":       safe_int(cols[9].get_text().strip()),
            "Goals Against":   safe_int(cols[10].get_text().strip()),
            "Goal Difference": safe_int(cols[11].get_text().strip()),
            "Form":            parse_form(cols[12]) if len(cols) > 12 else "",
        })
    return rows


@click.command()
@click.option(
    "--league", "-l", default="j1_east",
    type=click.Choice(list(LEAGUE_CONFIG.keys())),
    help="League group to scrape",
)
@click.option("--year", "-y", default=current_year, help="Season year (used for cache and output paths)")
@click.option("--download_dir", default="downloads", help="Directory for cached HTML files")
@click.option("--output_dir", default="tables", help="Base directory for JSON output")
def main(league, year, download_dir, output_dir):
    """Scrape J.League standings for one regional group and write JSON output."""
    cache_key, url, section_id = LEAGUE_CONFIG[league]

    os.makedirs(download_dir, exist_ok=True)
    out_path = os.path.join(output_dir, str(year))
    os.makedirs(out_path, exist_ok=True)

    html = fetch_page(url, cache_key, download_dir, year)
    if html is None:
        raise SystemExit(1)

    table = parse_section(html, section_id)
    if table is None:
        raise SystemExit(1)

    json_file = os.path.join(out_path, f"{league}.json")
    with open(json_file, "w") as f:
        json.dump(table, f, indent=2, ensure_ascii=False)
    print(f"Written {len(table)} teams to {json_file}")
    for row in table:
        print(f"  {row['Position']:2}. {row['Club']} ({row['Points']} pts)")


if __name__ == "__main__":
    main()
