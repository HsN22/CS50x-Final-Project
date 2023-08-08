import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table

def convert_excel_to_database(excel_file, database_file):
    # Step 1: Read data from Excel into a DataFrame
    df = pd.read_excel(excel_file, engine='openpyxl')

    # Step 2: Define SQLAlchemy metadata and engine
    engine = create_engine(f'sqlite:///{database_file}', echo=True)

    # Step 3: Create SQLAlchemy table from DataFrame with a unique table name
    table_name = excel_file.split('.')[0]  # Use the filename without the extension as the table name
    metadata = MetaData()
    your_data_table = Table(table_name, metadata,
        Column('id', Integer, primary_key=True),
        # Replace 'column1', 'column2', etc. with your actual column names from the Excel file
        Column('column1', String),
        Column('column2', Integer),
        # Add more columns as needed
    )

    metadata.create_all(engine)

    # Step 4: Insert data from DataFrame into the table
    df.to_sql(table_name, engine, if_exists='replace', index=False)

if __name__ == "__main__":
    excel_files = ['PressureL.xlsx', 'PressureV.xlsx', 'TemperatureL.xlsx', 'TemperatureV.xlsx']
    database_file = 'database.db'  # Replace 'your_database.db' with your desired database name

    for file in excel_files:
        convert_excel_to_database(file, database_file)
