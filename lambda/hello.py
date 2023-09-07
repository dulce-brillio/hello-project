import os
import psycopg2 as psy

def handler(event, context):
    db_endpoint = os.environ["DB_ENDPOINT"]
    db_port = os.environ["DB_PORT"]
    db_user = os.environ["DB_USER"]
    db_password = os.environ["DB_PASSWORD"]

    connection = psy.connect(
        host=db_endpoint,
        port=db_port,
        user=db_user,
        db_password=db_password,
        database="postgres"
    )

    cursor = connection.cursor()

    # Create new db
    cursor.execute("CREATE DATABASE IF NOT EXISTS my_database;")
    cursor.execute("USE my_database;")

    # Create a sample table
    cursor.execute("CREATE TABLE IF NOT EXISTS sample_table (id serial PRIMARY KEY, data varchar);")
    connection.commit()
    cursor.close()
    connection.close()

    return "Database and table created succesfully"
