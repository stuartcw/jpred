#!/usr/bin/env python3

import pandas as pd
import sqlite3

def csv_to_sqlite(csv_file_path, sqlite_db_path, table_name):
    """
    Reads a CSV file into a pandas DataFrame and inserts it into an SQLite database.

    Parameters:
    - csv_file_path: The file path of the CSV file.
    - sqlite_db_path: The file path of the SQLite database.
    - table_name: The name of the table where the CSV data will be inserted.
    """
    # Read the CSV file
    df = pd.read_csv(csv_file_path)

    # Connect to the SQLite database
    conn = sqlite3.connect(sqlite_db_path)

    # Write the data to a SQLite table
    df.to_sql(table_name, conn, if_exists='replace', index=False)

    # Close the database connection
    conn.close()
    print(f"Data from {csv_file_path} has been inserted into {table_name} table in {sqlite_db_path} database.")

# Example usage
if __name__ == "__main__":
    csv_file_path = 'JPred 2024 - Form responses 1.csv'  # Update this to the path of your CSV file
    sqlite_db_path = 'jpred.db'  # Update this to your SQLite database path
    table_name = 'jpred'  # Define the table name you want to use

    csv_to_sqlite(csv_file_path, sqlite_db_path, table_name)

