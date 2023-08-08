import sqlite3

import pandas as pd
from sqlalchemy import create_engine

def convert_excel_to_database(excel_file, database_file):
    # Step 1: Read data from Excel into a DataFrame
    df = pd.read_excel(excel_file, engine='openpyxl')

    # Step 2: Create a SQLite database engine using SQLAlchemy
    engine = create_engine(f'sqlite:///{database_file}', echo=True)

    # Step 3: Write DataFrame to the database as a table
    table_name = excel_file.split('.')[0]  # Use the filename without the extension as the table name
    df.to_sql(table_name, engine, if_exists='replace', index=False)

if __name__ == "__main__":
    excel_files = ['PressureL.xlsx', 'PressureV.xlsx', 'TemperatureL.xlsx', 'TemperatureV.xlsx']
    database_file = 'database.db'

    for file in excel_files:
        convert_excel_to_database(file, database_file)



