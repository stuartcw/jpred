#!/usr/bin/env python3
import click
import sys
import sqlite3
from jinja2 import Environment, FileSystemLoader

from icecream import ic
from collections import defaultdict

# Create a nested defaultdict
leaderboard = defaultdict(lambda: defaultdict(int))

# Function to connect to the SQLite database
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as e:
        print(e)
    return conn


def get_all_users(conn):
    cursor = conn.cursor()
    cursor.execute(f'''SELECT Name FROM jpred''')
    # return as a list strings
    return [row["Name"] for row in cursor.fetchall()]

league_predictions= { 
    "j1": [
        "J1 First Place",
        "J1 Second Place",
        "J1 Third Place",
        "J1 Third from Last Place",
        "J1 Second from Last Place",
        "J1 Last Place"
    ],
    "j2": [
        "J2 First Place",
        "J2 Second Place",
        "J2 Third Place",
        "J2 FORTH Place",
        "J2 FIFTH Place",
        "J2 SIXTH Place",
        "J2 Third from Last Place",
        "J2 Second from Last Place",
        "J2 Last Place"
     ],
    "j3": [
        "J3 First Place",
        "J3 Second Place",
        "J3 Third Place",
        "J3 FORTH Place",
        "J3 FIFTH Place",
        "J3 SIXTH Place",
        "J3 Third from Last Place",
        "J3 Second from Last Place",
        "J3 Last Place"
    ]
}

def j1_score(index):
    if index < 4:
        return f"""CASE
          WHEN position = {index} THEN 1 ELSE 0 END
          + CASE WHEN position IN (1, 2, 3) THEN 1 ELSE 0
            END"""
    else:
        return f"""CASE
          WHEN position = {index+11} THEN 1 ELSE 0 END
          + CASE WHEN position IN (18, 19, 20 ) THEN 1 ELSE 0
            END"""

def j2_j3_score(index):
    if index < 7:
        return f"""CASE
          WHEN position = {index} THEN 1 ELSE 0 END
          + CASE WHEN position IN (1, 2, 3, 4, 5, 6) THEN 1 ELSE 0
            END"""
    else:
        return f"""CASE
          WHEN position = {index+11} THEN 1 ELSE 0 END
          + CASE WHEN position IN (18, 19, 20 ) THEN 1 ELSE 0
            END"""


score_criteria={ 
                "j1": j1_score,
                "j2": j2_j3_score,
                "j3": j2_j3_score
        }


def make_league_score_SQL(name,league,year):
    table=f"{league}_{year}"
    sql_unions=[]

    for index, prediction_name in enumerate(league_predictions[league],start=1):
        #nic(index, prediction_name)

        ONE_PREDICTION_SQL=f"""
        SELECT {index} as "Index", Position, Prediction, Team, Position, 
            {score_criteria[league](index)} Score FROM
            (
            SELECT *, (SELECT Position FROM {table} WHERE {table}.Team = prediction.Team) AS Position 
            FROM (SELECT 
                    Name, 
                    [Email address] as Email, 
                    {index} AS "Order", 
                    '{prediction_name.title()}' as Prediction , 
                    [{prediction_name}] AS Team
                FROM jpred
                WHERE Name = '{name}'
            ) as prediction )"""

        sql_unions.append(ONE_PREDICTION_SQL)


    #ic(sql_unions)
    return " UNION ".join(sql_unions)

def query_database(conn, sql):
    cursor = conn.cursor()
    cursor.execute(sql)
    return cursor



def write_one_user(conn,name,html_filename,env,year=2024):
    ic(name)
    leagues =  ["j1","j2","j3"]
    total_score= 0
    total_exact_matches=0

    predictions= {}

    # Load Jinja environment and template
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('templates/user_template.html')

    if conn is None:
        print('Error! Cannot connect to the database.')
        sys.exit()
    else:
        with open(html_filename,"w") as html_file:
            for league in leagues:
                predictions[league]=[]
                sql=make_league_score_SQL(name,league,year)
                cursor = query_database(conn, sql)

                while row := cursor.fetchone() :
                    row_dict = {key: row[key] for key in row.keys()}
                    # ic(row_dict)
                    predictions[league].append(row_dict)

                #ic(predictions)
                scores=[ int(row["Score"]) for row  in predictions[league]]
                score_for_this_league =sum(scores)
                exact_matches= scores.count(2)
                leaderboard[name][league]=score_for_this_league
                total_score += score_for_this_league
                total_exact_matches += exact_matches

            leaderboard[name]["total_score"]=total_score
            leaderboard[name]["total_exact_matches"]=total_exact_matches
            html_content = template.render(predictions=predictions, name=name, league=league, total_score=total_score, year=year)
            html_file.write(html_content)
        print(f'HTML file {html_filename} has been created with the query results.')

def _main():
    print(make_league_score_SQL("Stuart Woodward","j3","2024"))

def main():
    db_path = 'jpred.db'
    # Load Jinja environment and template
    env = Environment(loader=FileSystemLoader('.'))
    
    conn = create_connection(db_path)
    names=get_all_users(conn)
    for name in names: # $$
        # ic(name)
        html_filename = "docs/preds/"+name+".html"
        if name.find("/") > 0:
            ic(f"Skipping {name} as it contains a /")
            continue
        write_one_user(conn,name,html_filename,env)
    # Render the HTML content using the template

    ordered_leaderboard=[]

    def sort_key(item):
        return (item[2]["total_score"] , item[2]["total_exact_matches"],item[2]["j1"],item[2]["j2"],item[2]["j3"])


    for name in leaderboard:
        ordered_leaderboard.append((leaderboard[name]["total_score"],name,leaderboard[name]))
    ordered_leaderboard=sorted(ordered_leaderboard, reverse=True, key=sort_key)
    
    template = env.get_template('templates/users.html')
    html_content = template.render(ordered_leaderboard=ordered_leaderboard)
    html_filename="docs/users.html"
    with open(html_filename,"w") as html_file:
        html_file.write(html_content)

    ic(ordered_leaderboard)
    

if __name__ == '__main__':
    main()

