import os
import pyodbc


def get_sqlserver_connection():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return pyodbc.connect(database_url)

    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={os.getenv('SQL_SERVER_HOST')};"
        f"DATABASE={os.getenv('SQL_SERVER_DB')};"
        f"UID={os.getenv('SQL_SERVER_USER')};"
        f"PWD={os.getenv('SQL_SERVER_PASSWORD')};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=yes;"
    )

    return pyodbc.connect(conn_str)
