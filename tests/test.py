from sqlite3 import connect
import sys
import os
from time import sleep
import pytest
import psycopg2
from testcontainers.postgres import PostgresContainer

# Add the src folder to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from app import *
# Path to the SQL initialization file
INIT_SQL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../sql/init.sql'))

# Setup mock database
postgres = PostgresContainer("postgres:17-alpine")



# Start the PostgreSQL container
postgres.start()

# Stop the container after all tests
def remove_container():
    postgres.stop()

# Set environment variables
os.environ["POSTGRES_HOST"] = postgres.get_connection_url()
os.environ["POSTGRES_PORT"] = postgres.get_exposed_port(5432)

# Connect to the default "postgres" database with autocommit enabled
admin_conn = psycopg2.connect(
    host=postgres.get_container_host_ip(),
    port=postgres.get_exposed_port(5432),
    user=postgres.username,
    password=postgres.password,
    dbname="postgres"  # Default admin database
)
admin_conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
admin_cursor = admin_conn.cursor()
# Create the `bude_transactions` database
admin_cursor.execute("CREATE DATABASE bude_transactions;")
admin_cursor.close()
admin_conn.close()


# Initialize the database with SQL script
conn = psycopg2.connect(
    host=postgres.get_container_host_ip(),
    port=postgres.get_exposed_port(5432),
    user=postgres.username,
    password=postgres.password,
    dbname="bude_transactions"
)
conn.autocommit = True
cursor = conn.cursor()
# Read and execute the SQL script
with open(INIT_SQL_PATH, "r") as sql_file:
    sql_script = sql_file.read()
    cursor.execute(sql_script)

cursor.execute("CREATE TABLE test(id INT PRIMARY KEY);")
cursor.close()
conn.close()

print(f"Host: {postgres.get_container_host_ip()}")
print(f"Port: {postgres.get_exposed_port(5432)}")

conn = psycopg2.connect(
    host=postgres.get_container_host_ip(),
    port=postgres.get_exposed_port(5432),
    user="public_user",
    password='supersecurepassword',
    dbname="bude_transactions"
)
cursor = conn.cursor()
cursor.execute("SELECT * FROM account;")
print(cursor.fetchall())
cursor.close()
conn.close()

while True:
    sleep(1)


 