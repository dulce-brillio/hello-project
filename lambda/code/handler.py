import os
import psycopg2 as psy
import boto3

def handler(event, context):
    db_endpoint = os.environ["DB_ENDPOINT"]
    db_port = os.environ["DB_PORT"]
    db_user = os.environ["DB_USER"]
    db_password_secret = os.environ["DB_PASSWORD_SECRET"]

    try:
    # Retrive secret
        client = boto3.client('secretsmanager')
        response = client.get_secret_value(SecretId=db_password_secret)
        db_password = response["SecretString"]

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
        cursor.execute("GRANT ALL ON sample_table TO mydbuser;")
        connection.commit()
        cursor.close()
        connection.close()

        return "Database and table created succesfully"
    except Exception as error:
        print ("Oops! An exception has occured:", error)
        print ("Exception TYPE:", type(error))
        return "error"
