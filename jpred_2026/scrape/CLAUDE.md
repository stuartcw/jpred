 defer to ~/.claude/CLAUDE.md

Use the existing scrape.py as reference but make it scrape the JLeague site for this special competition.

This year is a special year. We need to scrape:

J1_EAST from: https://www.jleague.jp/standings/j1/
J1_WEST from: https://www.jleague.jp/standings/j1/

J2_3_EAST_A from: https://www.jleague.jp/standings/j2j3/
J2_3_EAST_B from: https://www.jleague.jp/standings/j2j3/

J2_3_WEST_A from: https://www.jleague.jp/standings/j2j3/
J2_3_WEST_B from: https://www.jleague.jp/standings/j2j3/

Later there will be playoffs to determine the J1 winner and J2_3 winner.

# Initially implement

./scrape.py --league j1
./scrape.py --league j2_3_east_a
./scrape.py --league j2_3_east_b
./scrape.py --league j2_3_west_a
./scrape.py --league j2_3_west_b

Ensure that you only download each webpage once a day and continue to use the cached html for subsequent processing.
