#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests",
#     "beautifulsoup4",
#     "pandas",
#     "click",
#     "icecream",
# ]
# ///


import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import json
from icecream import ic
import click


def safe_int(value):
    """Convert value to an integer, returning 0 if conversion fails."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


current_year = datetime.now().year


def download_table(data_url, download_dir, league, year=current_year):

    ic(data_url)
    html_filename = f"{download_dir}/{league}_{year}.html"
    meta_filename = f"{download_dir}/{league}_{year}_meta.json"

    use_cache = False
    html_content = None

    # Check if both cache files exist
    if os.path.exists(html_filename) and os.path.exists(meta_filename):
        try:
            with open(meta_filename, "r") as f:
                meta = json.load(f)
                cached_last_modified = meta.get("last_modified")
                cached_time = datetime.fromisoformat(meta["timestamp"])
                current_time = datetime.now()

                ic("Check if cache is still valid (less than a day old)")
                if (current_time - cached_time).total_seconds() < 86400:
                    use_cache = True
                    ic("Use cache.")
                else:
                    ic("Cache is stale; check server for Last-Modified")
                    try:
                        ic("Try HEAD request first")
                        headers_response = requests.head(data_url)
                        if headers_response.status_code != 200:
                            ic(
                                "Can't retrieve HEAD -  Fallback to GET without downloading body"
                            )
                            headers_response = requests.get(data_url, stream=True)
                            headers_response.close()
                        last_modified = headers_response.headers.get("Last-Modified")
                    except requests.exceptions.RequestException as e:
                        print(f"Error checking server headers: {e}")
                        ic("Use stale cache as fallback")
                        use_cache = True
                    else:
                        if last_modified and last_modified == cached_last_modified:
                            ic("Server content hasn't changed; renew cache timestamp")
                            meta["timestamp"] = datetime.now().isoformat()
                            with open(meta_filename, "w") as f:
                                json.dump(meta, f)
                            use_cache = True
                        else:
                            ic(
                                "Server content has changed or Last-Modified not present - downloading fresh"
                            )
                            use_cache = False
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error reading metadata file: {e}. Proceeding to download.")
            use_cache = False

    if use_cache:
        ic("Read from cache")
        with open(html_filename, "r", encoding="utf-8") as f:
            html_content = f.read()
    else:
        ic("Download new content.")
        response = requests.get(data_url)
        if response.status_code != 200:
            print(f"Failed to retrieve the page. Status code: {response.status_code}")
            return None
        html_content = response.text
        # Save HTML to cache
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        # Save metadata
        last_modified = response.headers.get("Last-Modified")
        meta = {"last_modified": last_modified, "timestamp": datetime.now().isoformat()}
        ic(meta["last_modified"])
        ic(meta["timestamp"])
        with open(meta_filename, "w") as f:
            json.dump(meta, f)

    # Parse HTML content
    soup = BeautifulSoup(html_content, "html.parser")
    table = soup.find("table", class_="standing-table")

    if not table:
        print("No standings table found.")
        return None

    # Process the table rows
    league_table = []
    for row in table.find("tbody").find_all("tr"):
        cols = row.find_all("td")
        team_data = {
            "Position": safe_int(cols[0].text.strip()),
            "Club": cols[1].text.strip(),
            "Played": safe_int(cols[2].text.strip()),
            "Won": safe_int(cols[3].text.strip()),
            "Drawn": safe_int(cols[4].text.strip()),
            "Lost": safe_int(cols[5].text.strip()),
            "Goals For": safe_int(cols[6].text.strip()),
            "Goals Against": safe_int(cols[7].text.strip()),
            "Goal Difference": safe_int(cols[8].text.strip()),
            "Points": safe_int(cols[9].text.strip()),
            "Form": "".join(item.text.strip() for item in cols[10].find_all("div")),
        }
        league_table.append(team_data)

    return league_table


@click.command()
@click.option(
    "--league", "-l", default="j1", help="League to scrape (e.g., j1, j2, j3)"
)
@click.option("--year", "-y", default=current_year, help="Year to scrape data from")
@click.option(
    "--download_dir_base",
    "-b",
    default="downloads",
    help="Base directory for downloaded html files",
)
@click.option(
    "--output_dir_base", "-b", default="tables", help="Base directory for output files"
)
@click.option(
    "--data_url_base", "-d", default="https://www.jleague.co/standings", help=""
)
def main(league, year, output_dir_base, data_url_base, download_dir_base):
    """Scrape J.League standings data."""
    # Create base directory if it doesn't exist

    data_url = f"{data_url_base}/{league}/{year}/"

    download_dir = os.path.join(download_dir_base, f"{year}/{league}")
    if not os.path.exists(download_dir):
        os.makedirs(download_dir, exist_ok=True)

    output_dir = os.path.join(output_dir_base, f"{year}")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Set global output directory for downloads
    # global html_filename
    # html_filename = os.path.join(download_dir, f"{league}_{year}.html")

    league_table = download_table(data_url, download_dir, league, year)

    if league_table is not None:
        output_file_path = os.path.join(output_dir, f"{league}.json")
        ic(output_file_path)
        with open(output_file_path, "w") as f:
            json.dump(league_table, f, indent=2)
        for row in league_table:
            print(row)
    else:
        print("Failed to retrieve league table.")


if __name__ == "__main__":
    main()
