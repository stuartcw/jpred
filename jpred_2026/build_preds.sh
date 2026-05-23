#!/bin/bash
# build_preds.sh
#
# Import JPred predictions from the Google Form TSV export and generate
# per-user prediction HTML pages in docs/preds/.
#
# Prerequisites:
#   - A TSV file matching *2026*.tsv in the project root (Google Form export)
#   - Optionally: league standings JSON in tables/2026/ for scoring
#     (run scrape/update_tables.sh to produce these; scores show as '-' without them)
#
# Output:
#   - jpred_2026.db         SQLite database with predictions (and standings if available)
#   - docs/preds/*.html     One HTML page per participant
#   - docs/users.html       Index page listing all participants
#
# Usage:
#   ./build_preds.sh

set -e

# Detect year from the TSV filename (e.g. "Jpred 2026 - ....tsv" -> 2026)
TSV=$(ls *.tsv 2>/dev/null | head -1)
if [ -z "$TSV" ]; then
    echo "Error: No TSV file found in current directory."
    echo "Export the Google Form responses as a TSV and place it here."
    exit 1
fi

YEAR=$(echo "$TSV" | grep -oE '[0-9]{4}' | head -1)
if [ -z "$YEAR" ]; then
    echo "Error: Could not determine year from TSV filename: $TSV"
    exit 1
fi

echo "Year: $YEAR"
echo "Predictions file: $TSV"

mkdir -p docs/preds

echo ""
echo "Step 1: Import predictions from TSV into database..."
rm -f "jpred_${YEAR}.db"
./import.py "$YEAR"

echo ""
if [ -d "tables/$YEAR" ]; then
    echo "Step 2: Import league standings from JSON into database..."
    ./json_to_db.py "$YEAR"
else
    echo "Step 2: Skipped (tables/$YEAR/ not found - scores will show as '-')"
    echo "        Run scrape/update_tables.sh when standings are available."
fi

echo ""
echo "Step 3: Generate aggregate prediction summary pages..."
for GROUP in j1_winner j1_east j1_west j2_3_winner j2_3_east_a j2_3_east_b j2_3_west_a j2_3_west_b; do
    ./jpred.py --year "$YEAR" "docs/${GROUP}.html" "cols/${GROUP}.cols"
done

echo ""
echo "Step 4: Generate team A-Z report..."
./jpred_teams.py --year "$YEAR"

echo ""
echo "Step 5: Generate per-user prediction pages..."
./jpred_users.py --year "$YEAR"

cp style.css docs/style.css

echo ""
echo "Done. Pages written to docs/ and docs/preds/"
