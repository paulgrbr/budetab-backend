import sys
import os
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


@pytest.fixture(scope="function", autouse=True)
def setup(request):
    # Start the PostgreSQL container
    postgres.start()

    # Stop the container after all tests
    def remove_container():
        postgres.stop()

    request.addfinalizer(remove_container)

    # Set environment variables
    os.environ["POSTGRES_HOST"] = postgres.get_container_host_ip()
    os.environ["POSTGRES_PORT"] = postgres.get_exposed_port(5432)

    print(f"POSTGRES_HOST: {os.environ.get('POSTGRES_HOST')}")
    print(f"POSTGRES_PORT: {os.environ.get('POSTGRES_PORT')}")
    print(f"POSTGRES_DB_NAME: {os.environ.get('POSTGRES_DB_NAME')}")
    print(f"POSTGRES_PUBLIC_USER: {os.environ.get('POSTGRES_PUBLIC_USER')}")
    print(f"POSTGRES_PUBLIC_PW: {os.environ.get('POSTGRES_PUBLIC_PW')}")

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
    # Drop and recreate the public schema
    admin_cursor.execute("CREATE DATABASE bude_transactions;")
    admin_cursor.close()
    admin_conn.close()


@pytest.fixture(scope="function", autouse=True)
def setup_schema():
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
        sql_script = sql_file.read().format(db_public_user=os.environ['POSTGRES_PUBLIC_USER'], 
                                            db_public_user_pw=os.environ['POSTGRES_PUBLIC_PW']
                                            )
        cursor.execute(sql_script)
    conn.commit()
    cursor.close()
    conn.close()