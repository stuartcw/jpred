#!python3

import json

league="j2"

with open(f"{league}.json",  'r', encoding='utf-8') as league_data_file:
    league_data=json.load(league_data_file)

    for row in league_data:
        print(row["Position"],row["Club"],)
