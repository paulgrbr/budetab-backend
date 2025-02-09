from flask_jwt_extended import create_access_token
import sys
import os
import pytest
import psycopg2
from testcontainers.postgres import PostgresContainer
from flask_jwt_extended import create_access_token, create_refresh_token

# Add the src folder to the Python path
sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../src')))

from app import app  # noqa

# Path to the SQL initialization file
INIT_SQL_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../sql/init.sql.template'))


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
    admin_conn.set_isolation_level(
        psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
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
                                            db_public_user_pw=os.environ['POSTGRES_PUBLIC_PW'],
                                            db_auth_user=os.environ['POSTGRES_AUTH_USER'],
                                            db_auth_user_pw=os.environ['POSTGRES_AUTH_PW']
                                            )
        cursor.execute(sql_script)
    conn.commit()
    cursor.close()
    conn.close()


def init_mock_sql(file_path):
    # Read mock file into DB
    FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), file_path))
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
    with open(FILE, "r") as sql_file:
        sql_script = sql_file.read()
        cursor.execute(sql_script)
    cursor.close()
    conn.close()


@pytest.fixture(scope="function")
# Initialize the database with SQL script
def setup_account_entry():
    MOCK_FILE = '../sql/mock_account.sql'
    init_mock_sql(MOCK_FILE)


@pytest.fixture(scope="function")
# Initialize the database with SQL script
def setup_user_entry():
    MOCK_FILE = '../sql/mock_user.sql'
    init_mock_sql(MOCK_FILE)


def get_mock_JWT_access_token(is_admin: bool, identity: str = None):
    with app.app_context():
        if identity is None:
            identity = "d0192fdf-56ee-4aab-81e2-36667414c0b1"  # Default UUID

        permissions = "admin" if is_admin else "user"

        return create_access_token(identity=identity, fresh=True, additional_claims={"permissions": permissions})


def get_mock_JWT_refresh_token():
    with app.app_context():
        return create_refresh_token(identity="07b05ff3-0d08-4bad-9ea3-4d46f0a4f5d2", fresh=True)
