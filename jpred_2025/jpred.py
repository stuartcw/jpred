#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click",
#     "jinja2",
# ]
# ///
"""
Generate HTML pages from JPred prediction database.

This module queries an SQLite database containing JPred predictions and generates
HTML pages showing aggregated statistics for each prediction category (e.g., J1 First Place,
J2 Relegation, etc.). It uses Jinja2 templates to render the results and automatically
detects the year from the tables/ directory structure.

Usage:
    jpred.py <html_filename> <columns_file>

Example:
    jpred.py j1.html j1.cols
"""
import click
import sqlite3
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

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
    # Auto-detect year from tables directory structure
    tables_dir = Path('tables')
    year_dirs = [d for d in tables_dir.iterdir() if d.is_dir() and d.name.isdigit()]

    if not year_dirs:
        print("Error: No year directory found in tables/")
        exit(1)

    year = year_dirs[0].name
    db_path = f'jpred_{year}.db'
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
        html_content = template.render(data=data, year=year)

        # Write the HTML content to the specified file
        with open(html_filename, 'w') as html_file:
            html_file.write(html_content)

        print(f'HTML file {html_filename} has been created with the query results.')
    else:
        print('Error! Cannot connect to the database.')

if __name__ == '__main__':
    main()

