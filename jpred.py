#!/usr/bin/env python3
import click
import sqlite3
from jinja2 import Environment, FileSystemLoader

# Function to connect to the SQLite database
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)
    return conn

# Function to perform the query and return results
def query_database(conn, column):
    cur = conn.cursor()
    cur.execute(f"""SELECT "{column}", COUNT(*) as count FROM jpred GROUP BY "{column}" ORDER BY count DESC""")
    return cur.fetchall()

def custom_title_case(text):
    exceptions = {"and", "the", "of", "in", "on"}
    words = text.split()
    result = [
        word.capitalize() if word.lower() not in exceptions or i == 0 else word.lower()
        for i, word in enumerate(words)
    ]
    return " ".join(result)

@click.command()
@click.argument('html_filename')
@click.argument('columns_file')
def main(html_filename, columns_file):
    db_path = 'jpred.db'
    conn = create_connection(db_path)
    if conn is not None:
        with open(columns_file, 'r') as file:
            columns = file.read().splitlines()

        data = {}
        for column in columns:
            results = query_database(conn, column)
            data[custom_title_case(column)] = results

        # Load Jinja environment and template
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template('templates/template.html')

        # Render the HTML content using the template
        html_content = template.render(data=data)

        # Write the HTML content to the specified file
        with open(html_filename, 'w') as html_file:
            html_file.write(html_content)

        print(f'HTML file {html_filename} has been created with the query results.')
    else:
        print('Error! Cannot connect to the database.')

if __name__ == '__main__':
    main()

