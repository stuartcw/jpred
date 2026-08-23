# Running the JPred 2026 Scraper

The scraper fetches live standings from the J.League website and saves them as JSON files used to score predictions.

## Quick start

```bash
cd jpred_2026/scrape
bash update_tables.sh
```

This scrapes all six groups and writes JSON to `tables/2026/`. It also records the scrape time in `tables/2026/last_scraped.txt`, which is displayed on the site as "Standings last updated: YYYY-MM-DD HH:MM JST".

After scraping, rebuild the site:

```bash
cd ..
bash build_preds.sh
```

## What gets scraped

| Group | Source URL |
|-------|-----------|
| J1 East | https://www.jleague.jp/standings/j1/ |
| J1 West | https://www.jleague.jp/standings/j1/ |
| J2/J3 East-A | https://www.jleague.jp/standings/j2j3/ |
| J2/J3 East-B | https://www.jleague.jp/standings/j2j3/ |
| J2/J3 West-A | https://www.jleague.jp/standings/j2j3/ |
| J2/J3 West-B | https://www.jleague.jp/standings/j2j3/ |

The J1 page and the J2/J3 page are each downloaded once and cached. Both J1 groups share the same cached HTML, as do all four J2/J3 groups.

## Caching

Downloaded HTML is cached in `scrape/downloads/` for 24 hours. If the cache is fresh, the scraper uses it without making a network request. If it is stale, the scraper checks the server's `Last-Modified` header — if the page has not changed, the cache is refreshed without re-downloading.

To force a fresh download, delete the relevant cache files:

```bash
rm scrape/downloads/j1_2026.html scrape/downloads/j1_2026_meta.json
rm scrape/downloads/j2j3_2026.html scrape/downloads/j2j3_2026_meta.json
```

## Scraping a single group

```bash
cd jpred_2026/scrape
./scrape.py --league j1_east
./scrape.py --league j1_west
./scrape.py --league j2_3_east_a
./scrape.py --league j2_3_east_b
./scrape.py --league j2_3_west_a
./scrape.py --league j2_3_west_b
```

## Output

Each run writes or overwrites one file per group:

```
tables/2026/j1_east.json
tables/2026/j1_west.json
tables/2026/j2_3_east_a.json
tables/2026/j2_3_east_b.json
tables/2026/j2_3_west_a.json
tables/2026/j2_3_west_b.json
tables/2026/last_scraped.txt
```

The JSON format is a list of team objects with `Position`, `Club` (Japanese name), `Points`, and match statistics. `build_preds.sh` calls `json_to_db.py` which translates Japanese club names to English using `jp_name_mapping.csv` before writing to the database.

## Troubleshooting

**"section not found" error** — The J.League website HTML structure may have changed. Check the live page source and update the section identifiers in `LEAGUE_CONFIG` in `scrape/scrape.py`.

**Team names not matching predictions** — If a newly promoted or renamed club does not appear in scoring, add it to `jp_name_mapping.csv` (Japanese name in the first column, English prediction name in the second).

**Stale standings** — If the site shows old standings after running the scraper, the 24-hour cache may still be valid even though the page has updated. Delete the cache files (see above) and re-run.
