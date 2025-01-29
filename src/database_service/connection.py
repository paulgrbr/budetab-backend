# Database private connection
import os
import psycopg2
from dotenv import load_dotenv
load_dotenv()

def get_auth_db_connection():
    conn = psycopg2.connect(host=os.environ['POSTGRES_HOST'],
                            port=os.environ['POSTGRES_PORT'],
                            database=os.environ['POSTGRES_DB_NAME'],
                            user=os.environ['POSTGRES_AUTH_USER'],
                            password=os.environ['POSTGRES_AUTH_PW'])
    return conn

# Database public connection for e.g. registering
def get_public_db_connection():
    conn = psycopg2.connect(host=os.environ['POSTGRES_HOST'],
                            port=os.environ['POSTGRES_PORT'],
                            database=os.environ['POSTGRES_DB_NAME'],
                            user=os.environ['POSTGRES_PUBLIC_USER'],
                            password=os.environ['POSTGRES_PUBLIC_PW'])
    
    return conn

