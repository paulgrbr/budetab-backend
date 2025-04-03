import os
import sys
import bcrypt
import uuid
import bcrypt
import psycopg2
from models.Account import Account, AccountSession

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


def create_account_session(token_id: uuid, origin_id: uuid, account_id: uuid,
                           ip_address: str, device: str, browser: str):
    try:
        conn = get_public_db_connection()
        cur = conn.cursor()

        cur.execute('''
                    INSERT INTO account_sessions(token_id, origin_id, account_id, ip_address, device, browser)
                    VALUES(%s, %s, %s, %s, %s, %s)
                    ''',
                    (
                        token_id,
                        origin_id,
                        account_id,
                        ip_address,
                        device,
                        browser
                    ))
        conn.commit()
        cur.close()
        conn.close()
        return

    except psycopg2.Error as Err:
        conn.rollback()
        conn.close()
        raise Err


def check_token_id_is_active(account_id: uuid, token_id: uuid):
    try:
        conn = get_public_db_connection()
        cur = conn.cursor()

        cur.execute('''
                    SELECT token_id
                    FROM account_sessions
                    WHERE token_id = %s
                    AND account_id = %s
                    AND invalidated = false
                    ''',
                    (
                        token_id,
                        account_id
                    ))
        response = cur.fetchall()
        cur.close()
        conn.close()
        if not response:
            return False
        else:
            return True

    except psycopg2.Error as Err:
        conn.rollback()
        conn.close()
        raise Err


def invalidate_token_by_token_id(account_id: uuid, token_id: uuid):
    try:
        conn = get_public_db_connection()
        cur = conn.cursor()

        cur.execute('''
                    UPDATE account_sessions
                    SET invalidated = true,
                        time_invalidated = NOW()
                    WHERE token_id = %s
                    AND account_id = %s
                    AND invalidated = false
                    ''',
                    (
                        token_id,
                        account_id
                    ))
        conn.commit()
        cur.close()
        conn.close()
        return

    except psycopg2.Error as Err:
        conn.rollback()
        conn.close()
        raise Err


def invalidate_tokens_by_origin_id(account_id: uuid, origin_id: uuid):
    try:
        conn = get_public_db_connection()
        cur = conn.cursor()

        cur.execute('''
                    UPDATE account_sessions
                    SET invalidated = true,
                        time_invalidated = NOW()
                    WHERE origin_id = %s
                    AND account_id = %s
                    AND invalidated = false
                    ''',
                    (
                        origin_id,
                        account_id
                    ))
        conn.commit()
        cur.close()
        conn.close()
        return

    except psycopg2.Error as Err:
        conn.rollback()
        conn.close()
        raise Err


def invalidate_tokens_by_account_id(account_id: uuid):
    try:
        conn = get_public_db_connection()
        cur = conn.cursor()

        cur.execute('''
                    UPDATE account_sessions
                    SET invalidated = true,
                        time_invalidated = NOW()
                    WHERE account_id = %s
                    AND invalidated = false
                    ''',
                    (
                        account_id,
                    ))
        conn.commit()
        cur.close()
        conn.close()
        return

    except psycopg2.Error as Err:
        conn.rollback()
        conn.close()
        raise Err


def get_all_account_sessions():
    conn = get_auth_db_connection()
    cur = conn.cursor()

    cur.execute('''
                SELECT token_id, account_id, ip_address, device, browser, origin_id, time_created
                FROM account_sessions
                WHERE invalidated = false
                ''')
    response = cur.fetchall()
    parsed_response = []
    for row in response:
        parsed_response.append(AccountSession(row[0], row[1], row[2], row[3], row[4], row[5], row[6]))
    cur.close()
    conn.close()

    return parsed_response


def cleanup_expired_sessions():
    try:
        conn = get_auth_db_connection()
        cur = conn.cursor()

        cur.execute('''
                    DELETE FROM account_sessions
                    WHERE (
                        invalidated = true
                        AND time_invalidated < NOW() - INTERVAL '10 days'
                    )
                    OR time_created < NOW() - INTERVAL '365 days';
                    ''')
        conn.commit()
        cur.close()
        conn.close()
        return

    except psycopg2.Error as Err:
        conn.rollback()
        conn.close()
        raise Err


def update_account_session_notification_token(account_id: str, origin_id: str, notification_token: str) -> int:
    try:
        conn = get_public_db_connection()
        cur = conn.cursor()

        cur.execute('''
                    UPDATE account_sessions
                    SET push_notification_key = %s
                    WHERE account_id = %s
                    AND origin_id = %s
                    AND invalidated = false
                    ''',
                    (
                        notification_token,
                        account_id,
                        origin_id
                    ))

        affected_rows = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        return affected_rows

    except psycopg2.Error as Err:
        conn.rollback()
        conn.close()
        raise Err


def get_all_admin_notification_keys():
    conn = get_auth_db_connection()
    cur = conn.cursor()

    cur.execute('''
                SELECT DISTINCT s.push_notification_key
                FROM account_sessions s
                JOIN account a ON a.public_id = s.account_id
                JOIN "user" u ON a.linked_user_id = u.user_id
                WHERE s.invalidated = false
                AND s.push_notification_key IS NOT NULL
                AND u.permissions = 'admin'
                ''')
    response = cur.fetchall()
    parsed_response = []
    for row in response:
        parsed_response.append(row[0])
    cur.close()
    conn.close()

    return parsed_response


def get_all_user_notification_keys():
    conn = get_auth_db_connection()
    cur = conn.cursor()

    cur.execute('''
                SELECT DISTINCT s.push_notification_key
                FROM account_sessions s
                JOIN account a ON a.public_id = s.account_id
                WHERE s.invalidated = false
                AND s.push_notification_key IS NOT NULL
                ''')
    response = cur.fetchall()
    parsed_response = []
    for row in response:
        parsed_response.append(row[0])
    cur.close()
    conn.close()

    return parsed_response


def get_one_users_notification_keys(user_id: uuid):
    conn = get_auth_db_connection()
    cur = conn.cursor()

    cur.execute('''
                SELECT DISTINCT s.push_notification_key
                FROM account_sessions s
                JOIN account a ON a.public_id = s.account_id
                JOIN "user" u ON a.linked_user_id = u.user_id
                WHERE s.invalidated = false
                AND s.push_notification_key IS NOT NULL
                AND u.user_id = %s
                ''',
                (
                    user_id,
                ))
    response = cur.fetchall()
    parsed_response = []
    for row in response:
        parsed_response.append(row[0])
    cur.close()
    conn.close()

    return parsed_response


def get_one_account_notification_keys(account_id: uuid):
    conn = get_auth_db_connection()
    cur = conn.cursor()

    cur.execute('''
                SELECT DISTINCT s.push_notification_key
                FROM account_sessions s
                JOIN account a ON a.public_id = s.account_id
                JOIN "user" u ON a.linked_user_id = u.user_id
                WHERE s.invalidated = false
                AND s.push_notification_key IS NOT NULL
                AND a.public_id = %s
                ''',
                (
                    account_id,
                ))
    response = cur.fetchall()
    parsed_response = []
    for row in response:
        parsed_response.append(row[0])
    cur.close()
    conn.close()

    return parsed_response
