import psycopg2
import sys
import os
import uuid
from models.User import User

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), './')))

from database_service.connection import *  # noqa


def get_user_by_linked_account_uuid(account_public_id: uuid):
    conn = get_auth_db_connection()
    cur = conn.cursor()
    cur.execute('''
                SELECT u.user_id, u.first_name, u.last_name, u.time_created, u.is_temporary, u.price_ranking, u.permissions
                FROM account a
                JOIN "user" u ON(a.linked_user_id = u.user_id)
                WHERE a.public_id = %s
                ''',
                (account_public_id, ))
    response = cur.fetchone()
    cur.close()
    conn.close()
    if response:
        return User(response[0], response[1], response[2], response[3],
                    response[4], response[5], response[6])
    else:
        return None


def create_user(first_name: str, last_name: str, is_temporary: bool, price_ranking: str, permissions: str):
    try:
        conn = get_auth_db_connection()
        cur = conn.cursor()

        # Generate a user UUID
        user_uuid = str(uuid.uuid4())
        cur.execute('''
                    INSERT INTO "user"(user_id, first_name, last_name, is_temporary, price_ranking, permissions)
                    VALUES(%s, %s, %s, %s, %s, %s)
                    ''',
                    (
                        user_uuid,
                        first_name,
                        last_name,
                        is_temporary,
                        price_ranking,
                        permissions

                    ))
        conn.commit()
        cur.close()
        conn.close()
        return {"error": None, "message": {"uuid": user_uuid, "firstName": first_name, "lastName": last_name}}

    except psycopg2.errors.UniqueViolation as Err:
        conn.rollback()
        conn.close()
        return {"error": {"exception": Err.__class__.__name__,
                          "message": "User already exists", "pgCode": Err.pgcode}, "message": None}

    except psycopg2.Error as Err:
        conn.rollback()  # Rollback in case of error
        conn.close()
        return {"error": {"exception": Err.__class__.__name__, "message": str(
            Err.diag.message_primary), "pgCode": Err.pgcode}, "message": None}


def get_all_users():
    conn = get_auth_db_connection()
    cur = conn.cursor()
    cur.execute('''
                SELECT u.user_id, u.first_name, u.last_name, u.time_created, u.is_temporary, u.price_ranking, u.permissions
                FROM "user" u
                '''
                )
    response = cur.fetchall()
    cur.close()
    conn.close()

    parsed_response = []
    for row in response:
        parsed_response.append(User(row[0], row[1], row[2], row[3],
                                    row[4], row[5], row[6]))
    return parsed_response


def delete_user_by_user_id(user_id: str):
    try:
        conn = get_auth_db_connection()
        cur = conn.cursor()
        cur.execute('''
            DELETE FROM "user"
            WHERE user_id = %s
            RETURNING user_id;
                    ''',
                    (user_id,))

        deleted_user = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        if deleted_user:
            return {"error": None, "message": f"User {user_id} deleted successfully"}, 200
        else:
            return {"error": {"exception": "UserNotFound", "message": "User not found"}, "message": None}, 404

    except psycopg2.Error as Err:
        conn.rollback()
        conn.close()
        return {"error": {"exception": Err.__class__.__name__, "message": str(
            Err.diag.message_primary), "pgCode": Err.pgcode}, "message": None}, 500


def update_user_profile_picture_path(user_id: uuid, path: str):
    try:
        conn = get_auth_db_connection()
        cur = conn.cursor()
        print(user_id, path)

        cur.execute('''
                    UPDATE "user"
                    SET profile_picture_path = %s
                    WHERE user_id = %s
                    ''',
                    (
                        path,
                        user_id,
                    ))
        conn.commit()
        cur.close()
        conn.close()
        return {"error": None, "message": {"status": "Picture uploaded successfully", "uuid": user_id}}

    except psycopg2.Error as Err:
        conn.rollback()
        conn.close()
        return {"error": {"exception": Err.__class__.__name__, "message": str(
            Err.diag.message_primary), "pgCode": Err.pgcode}, "message": None}


def get_profile_picture_path_by_user_id(user_id: uuid):
    conn = get_auth_db_connection()
    cur = conn.cursor()
    cur.execute('''
                SELECT profile_picture_path
                FROM "user"
                WHERE user_id = %s
                ''',
                (user_id, ))
    response = cur.fetchone()
    cur.close()
    conn.close()
    if response:
        return response[0]
    else:
        return None
