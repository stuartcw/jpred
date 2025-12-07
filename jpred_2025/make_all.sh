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
./jpred.py docs/j1.html j1.cols
./jpred.py docs/j2.html j2.cols
./jpred.py docs/j3.html j3.cols
./jpred_users.py
./generate_leaderboard_image.py
cp assets/favicons/*.png docs/ 2>/dev/null || true
cp assets/favicons/*.ico docs/ 2>/dev/null || true
cp assets/favicons/site.webmanifest docs/ 2>/dev/null || true
cp index.html docs/ 2>/dev/null || true
cp style.css docs/ 2>/dev/null || true
