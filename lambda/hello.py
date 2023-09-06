import json
import boto3
import psycopg2
import os

def create_table():
    create_table = """CREATE TABLE queries(
            id SERIAL PRIMARY KEY,
            query_date DATE
            )
            """
    try:
        cursor.execute(create_table)
        cursor.close()
        connection.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if connection is not None:
            connection.close()

def handler(event, context):
  connection = psycopg2.connect(user=os.environ['username'], password=os.environ['password'], host=credential['host'], database=credential['db'])
  cursor = connection.cursor()
  query = '''--initial database
    CREATE DATABASE postgrelearning;

    --create a schema
    CREATE SCHEMA sales;

    --show the search path for schemas
    SHOW search_path;

    --modify the search path
    SET search_path TO sales,public;

    --create a table with defaults and calculated column
    CREATE TABLE sales.saledetail
    (saledetailid int NOT NULL GENERATED BY DEFAULT AS IDENTITY,
    saledatetime TIMESTAMP DEFAULT NOW(),
    itemtotal MONEY,
    itemdiscount NUMERIC(2,2),
    saletotal MONEY GENERATED ALWAYS AS (itemtotal * itemdiscount) STORED,
    CONSTRAINT saledetailpk PRIMARY KEY (saledetailid));

    -- add data to the table
    INSERT INTO sales.saledetail
    (itemtotal,itemdiscount)
    VALUES
    (343.42,.95);

    -- retrieve the data
    SELECT * FROM sales.saledetail;
    '''
  cursor.execute(query)
  results = cursor.fetchone()
  cursor.close()
  connection.commit()
  return results