#!/bin/bash
# Optional year parameter
YEAR=$1

if [ -z "$YEAR" ]; then
    # Auto-detect year from tables directory
    YEAR=$(ls -d tables/*/ 2>/dev/null | head -1 | sed 's|tables/||;s|/||')

    if [ -z "$YEAR" ]; then
        echo "Error: No year directory found in tables/"
        exit 1
    fi
    echo "Auto-detected year: $YEAR"
else
    echo "Using specified year: $YEAR"
fi

rm -f jpred_${YEAR}.db
./import.py "$YEAR"
./json_to_db.py "$YEAR"
