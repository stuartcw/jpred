#!venv/bin/python3.12
import click
import sys
import sqlite3
from jinja2 import Environment, FileSystemLoader

from icecream import ic

# Function to connect to the SQLite database
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as e:
        print(e)
    return conn

# Function to perform the query and return results
def query_database(conn, name):
    cursor = conn.cursor()
    cursor.execute(f'''SELECT
  Timestamp,
  Name,
  "J1 First Place",
  "J1 Second Place",
  "J1 Third Place",
  "J1 Third from Last Place",
  "J1 Second from Last Place",
  "J1 Last Place",
  "J2 First Place",
  "J2 Second Place",
  "J2 Third Place",
  "J2 FORTH Place" as "J2 Forth Place",
  "J2 FIFTH Place" as "J2 Fifth Place",
  "J2 SIXTH Place" as "J2 Sixth Place",
  "J2 Third from Last Place",
  "J2 Second from Last Place",
  "J2 Last Place",
  "J3 First Place",
  "J3 Second Place",
  "J3 Third Place",
  "J3 FORTH Place" as "J3 Forth Place",
  "J3 FIFTH Place" as "J3 Fifth Place",
  "J3 SIXTH Place" as "J3 Sixth Place",
  "J3 Third from Last Place",
  "J3 Second from Last Place",
  "J3 Last Place"
FROM jpred
    WHERE Name LIKE "{name}"''')
    return cursor 

def write_one_user(conn,name,html_filename,env):
    ic(name)
    leagues = ["j1","j2","j3"]
    league_columns = []

    predictions={}
    for league in leagues:
        columns_file="columns/"+league+".cols"
        with open(columns_file, 'r') as file:
              columns: list[str]  = file.read().splitlines() 
              league_columns.append((league,columns))

    # Load Jinja environment and template
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('templates/user_template.html')

    if conn is not None:
       
        with open(html_filename,"w") as html_file:
            cursor = query_database(conn, name)
            while row := cursor.fetchone() :
                row_dict = {key: row[key] for key in row.keys()}
                
                for league,columns in league_columns:
                    table_row=[]
                    #ic(league,columns)
                    for column in columns:
                        #j1 = { key:value for key, value in row_dict.items() if key.startswith("J1") }
                        #ic(column,row[column])
                        table_row.append((column,row[column]))
                    #ic(30*"-")
                    predictions[league]=table_row

            #ic(predictions.keys())
            #ic(predictions["j1"])
            #ic(predictions["j2"])

            # Render the HTML content using the template
            html_content = template.render(predictions=predictions, name=name, league=league)
            html_file.write(html_content)

            print(f'HTML file {html_filename} has been created with the query results.')
    else:
        print('Error! Cannot connect to the database.')

def get_all_users(conn):
    cursor = conn.cursor()
    cursor.execute(f'''SELECT Name FROM jpred''')
    # return as a list strings
    return [row["Name"] for row in cursor.fetchall()]

def main():
    db_path = 'jpred.db'
    # Load Jinja environment and template
    env = Environment(loader=FileSystemLoader('.'))
    
    conn = create_connection(db_path)
    names=get_all_users(conn)
    for name in names:
        # ic(name)
        html_filename = "docs/preds/"+name+".html"
        if name.find("/") > 0:
            ic(f"Skipping {name} as it contains a /")
            continue
        write_one_user(conn,name,html_filename,env)
    # Render the HTML content using the template
    
    template = env.get_template('templates/users.html')
    html_content = template.render(names=names)
    html_filename="docs/users.html"
    with open(html_filename,"w") as html_file:
        html_file.write(html_content)
    

if __name__ == '__main__':
    main()

