#!/bin/bash
# Auto-detect year from tables directory
YEAR=$(ls -d tables/*/ 2>/dev/null | head -1 | sed 's|tables/||;s|/||')

if [ -z "$YEAR" ]; then
    echo "Error: No year directory found in tables/"
    exit 1
fi

echo "Using year: $YEAR"

mkdir -p docs
mkdir -p docs/preds
rm -f jpred_${YEAR}.db
rm -f docs/j*.html
rm -f docs/users.html
rm -f docs/preds/*.html
rm -f docs/leaderboard.png
./create_db.sh
for GROUP in j1_winner j1_east j1_west j2_3_winner j2_3_east_a j2_3_east_b j2_3_west_a j2_3_west_b; do
    ./jpred.py "docs/${GROUP}.html" "cols/${GROUP}.cols"
done
./jpred_users.py
./generate_leaderboard_image.py
cp assets/favicons/*.png docs/ 2>/dev/null || true
cp assets/favicons/*.ico docs/ 2>/dev/null || true
cp assets/favicons/site.webmanifest docs/ 2>/dev/null || true
cp index.html docs/ 2>/dev/null || true
cp style.css docs/ 2>/dev/null || true
