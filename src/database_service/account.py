import os
import sys
import uuid
import bcrypt
import psycopg2
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), './')))
from connection import *

def create_account(username: str, password: str):
    try:
        conn = get_public_db_connection()
        cur = conn.cursor()

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Generate a user UUID
        user_uuid = str(uuid.uuid4())
        cur.execute('''
                    INSERT INTO account(public_id, username, password_hash)
                    VALUES(%s, %s, %s)
                    ''', 
                    (
                    user_uuid,
                    username,
                    hashed_password
                    
                    ))
        conn.commit()
        cur.close()
        conn.close()
        return {"error": None, "message": {"uuid": user_uuid, "username": username}}
    
    except psycopg2.errors.UniqueViolation as Err:
        conn.close()
        return {"error": {"exception": Err.__class__.__name__, "message":"User already exists", "pgCode": Err.pgcode}, "message": None}
    
    except psycopg2.Error as Err:
        conn.close()
        return {"error": {"exception": Err.__class__.__name__, "message":str(Err.diag.message_primary), "pgCode": Err.pgcode}, "message": None}

def get_pg_version():
    conn = get_public_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT version();')
    version = cur.fetchone()
    cur.close()
    conn.close()
    return version