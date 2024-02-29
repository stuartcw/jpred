#!python3

import click
import sqlite3
from sqlite3 import Error
import os

# Function to connect to the SQLite database
def create_connection(db_file):
    """Create a database connection to the SQLite database specified by db_file"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    return conn

# Function to perform the query and return results
def query_database(conn, column):
    """Query the database for the specified column and return the results"""
    cur = conn.cursor()
    cur.execute(f"""SELECT "{column}", COUNT(*) as count FROM jpred GROUP BY "{column}" ORDER BY count DESC""")
    return cur.fetchall()

# Function to generate HTML content
def generate_html(results, column):
    """Generate HTML content from query results"""
    html_content = f'<h2>Results for {column.title()}</h2>'
    html_content += '<table border="1"><tr><th>Value</th><th>Count</th></tr>'
    for row in results:
        html_content += f'<tr><td>{row[0]}</td><td>{row[1]}</td></tr>'
    html_content += '</table>'
    return html_content

@click.command()
@click.argument('html_filename')
@click.argument('columns_file')
def main(html_filename, columns_file):
    """Main function to execute the query for each column and generate an HTML file with the results."""
    # Connect to the database
    db_path = 'jpred.db'
    conn = create_connection(db_path)
    if conn is not None:
        # Read the column names from the file
        with open(columns_file, 'r') as file:
            columns = file.read().splitlines()

        # Generate HTML content
        html_content = '<html><head><title>Database Query Results</title></head><body>'
        for column in columns:
            results = query_database(conn, column)
            html_content += generate_html(results, column)
        html_content += '</body></html>'

        # Write the HTML content to the specified file
        with open(html_filename, 'w') as html_file:
            html_file.write(html_content)

        print(f'HTML file {html_filename} has been created with the query results.')
    else:
        print('Error! Cannot connect to the database.')

if __name__ == '__main__':
    main()

