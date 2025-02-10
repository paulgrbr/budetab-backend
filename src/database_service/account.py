import os
import sys
import bcrypt
import uuid
import bcrypt
import psycopg2
from models.Account import Account

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), './')))

from database_service.connection import *  # noqa


def create_account(username: str, password: str):
    try:
        conn = get_public_db_connection()
        cur = conn.cursor()

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

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
        conn.rollback()
        conn.close()
        return {"error": {"exception": Err.__class__.__name__,
                          "message": "User already exists", "pgCode": Err.pgcode}, "message": None}

    except psycopg2.Error as Err:
        conn.rollback()
        conn.close()
        return {"error": {"exception": Err.__class__.__name__, "message": str(
            Err.diag.message_primary), "pgCode": Err.pgcode}, "message": None}


def get_pg_version():
    conn = get_public_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT version();')
    version = cur.fetchone()
    cur.close()
    conn.close()
    return version


def get_all_accounts_by_username(username: str):
    conn = get_public_db_connection()
    cur = conn.cursor()

    cur.execute('''
                SELECT public_id, username, password_hash, time_created, linked_user_id
                FROM account
                WHERE username = %s
                ''',
                (username, ))
    response = cur.fetchall()
    parsed_response = []
    for row in response:
        parsed_response.append(Account(row[0], row[1], row[2].tobytes(), row[3], row[4]))
    cur.close()
    conn.close()

    return parsed_response


def get_account_by_uuid(public_id: uuid):
    conn = get_public_db_connection()
    cur = conn.cursor()

    cur.execute('''
                SELECT public_id, username, time_created, linked_user_id
                FROM account
                WHERE public_id = %s
                ''',
                (public_id, ))
    response = cur.fetchone()
    cur.close()
    conn.close()
    return Account(response[0], response[1], None, response[2], response[3])


def update_link_user_to_account(public_id: uuid, user_id: uuid):
    try:
        conn = get_auth_db_connection()
        cur = conn.cursor()

        cur.execute('''
                    UPDATE account
                    SET linked_user_id = %s
                    WHERE public_id = %s
                    ''',
                    (
                        user_id,
                        public_id,
                    ))
        conn.commit()
        cur.close()
        conn.close()
        return {"error": None, "message": f"Linked account {public_id} successfully"}, 200

    except psycopg2.errors.UniqueViolation as Err:
        conn.rollback()
        conn.close()
        return {"error": {"exception": Err.__class__.__name__,
                          "message": "User already exists", "pgCode": Err.pgcode}, "message": None}

    except psycopg2.Error as Err:
        conn.rollback()
        conn.close()
        return {"error": {"exception": Err.__class__.__name__, "message": str(
            Err.diag.message_primary), "pgCode": Err.pgcode}, "message": None}


def get_all_accounts():
    conn = get_auth_db_connection()
    cur = conn.cursor()

    cur.execute('''
                SELECT public_id, username, time_created, linked_user_id
                FROM account
                ''')
    response = cur.fetchall()
    parsed_response = []
    for row in response:
        parsed_response.append(Account(row[0], row[1], "", row[2], row[3]))
    cur.close()
    conn.close()

    return parsed_response


def update_account_password(user_id: uuid, password: str):
    try:
        conn = get_auth_db_connection()
        cur = conn.cursor()

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cur.execute('''
                    UPDATE account
                    SET password_hash = %s
                    WHERE public_id = %s
                    ''',
                    (
                        hashed_password,
                        user_id,
                    ))
        conn.commit()
        cur.close()
        conn.close()
        return {"error": None, "message": {"uuid": user_id, "message": "Password changed successfully"}}

    except psycopg2.Error as Err:
        conn.rollback()
        conn.close()
        return {"error": {"exception": Err.__class__.__name__, "message": str(
            Err.diag.message_primary), "pgCode": Err.pgcode}, "message": None}
