from ipaddress import ip_address
from tabnanny import check
import token
import uuid
import bcrypt
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt, jwt_required, get_jwt_identity
import user_agents
from database_service.account import check_token_id_is_active, cleanup_expired_sessions, create_account, create_account_session, get_all_account_sessions, get_all_accounts, get_pg_version, get_all_accounts_by_username, get_account_by_uuid, invalidate_tokens_by_account_id, invalidate_tokens_by_origin_id, update_account_password, update_account_session_notification_token, update_link_user_to_account
from database_service.sqlstate import map_sqlstate_to_http_status
import re
from database_service.user import get_user_by_linked_account_uuid
from endpoints.fcm_service import fcm_notify_all_admins
from endpoints.jwt_handlers import roles_required
from models.Account import Account

accounts = Blueprint('accounts', __name__)

# RegEx patterns
usernamePattern = r"^[a-z0-9_]+$"
passwordPattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?!.*\s).{8,}$"


# Register user route
@accounts.route("/register", methods=['POST'])
def handle_register():
    try:
        # Parse JSON data
        data = request.get_json()

        # Extract and validate username and password
        username = data.get('username').strip().lower()
        password = data.get('password')
        if not username or not password:
            return jsonify({"error": {"exception": "MissingValues",
                           "message": "Missing username or password"}, "message": None}), 400

        # Check if pattern matches
        if not re.match(usernamePattern, username):
            return jsonify({"error": {"exception": "WrongUsernameFormat",
                           "message": "Username contains invalid characters"}, "message": None}), 400
        if not re.match(passwordPattern, password):
            return jsonify({"error": {"exception": "WrongPasswordFormat",
                           "message": "Password must at least be 8 characters long and contain upper and lowercase letters and numbers"}, "message": None}), 400

        # Create the account
        response = create_account(username, password)
        if response["error"]:
            return jsonify(response), map_sqlstate_to_http_status(response["error"]["pgCode"])
        else:
            fcm_notify_all_admins(
                "Neue Registrierung",
                f"👤 '{username}' hat sich gerade registriert. Bitte verknüpfe den Account.",
                sound=True,
                route="/admin/all-accounts",
            )
            return jsonify(response), 201

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


# Test connection to db
@accounts.route("/test-connection", methods=['GET'])
def handle_connection_is_alive():
    return jsonify(get_pg_version()), 200


# Account login route
@accounts.route("/login", methods=['POST'])
def handle_login():
    try:
        # Parse JSON data
        data = request.get_json()

        # Reuest metadata for sessions
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        ua_string = request.headers.get("User-Agent", "")
        ua = user_agents.parse(ua_string)
        device = f"{ua.device.family}"
        browser = f"{ua.browser.family} {ua.browser.version_string}"

        # Extract and validate username and password
        username = data.get('username').strip().lower()
        password = data.get('password')
        if not username or not password:
            return jsonify({"error": {"exception": "MissingValues",
                           "message": "Missing username or password"}, "message": None}), 400

        accounts = get_all_accounts_by_username(username)
        if accounts:
            account = accounts[0]
        else:
            account = None

        if account and bcrypt.checkpw(password.encode("utf-8"), account.password_hash):
            origin_id = data.get('originId')
            if origin_id:
                # Invalidate all other tokens for this users origin (browser, app, etc.)
                invalidate_tokens_by_origin_id(account.public_id, origin_id)
            else:
                # On first startup issue a new originId
                origin_id = str(uuid.uuid4())

            token_id = str(uuid.uuid4())

            response = create_account_session(token_id, origin_id, account.public_id, ip_address, device, browser)

            # Get user permissions if assigned
            user = get_user_by_linked_account_uuid(account.public_id)
            if user:
                additional_claims = {
                    "permissions": user.permissions
                }
            else:
                additional_claims = {
                    "permissions": "none"
                }

            access_token = create_access_token(
                identity=account.public_id, fresh=True, additional_claims=additional_claims)
            refresh_token = create_refresh_token(identity=account.public_id, additional_claims={
                "tokenId": token_id,
                "originId": origin_id
            })

            return jsonify({"error": None, 'message': 'Login Success',
                           'access_token': access_token, 'refresh_token': refresh_token, 'origin_id': origin_id}), 200
        else:
            return jsonify({"error": None, 'message': 'Login Failed'}), 401

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


# Account logout route
@accounts.route("/logout", methods=['POST'])
@jwt_required()
def handle_logout():
    try:
        # Parse JSON data
        data = request.get_json()

        # Extract the user ID from the JWT
        user_id = get_jwt_identity()

        origin_id = data.get('originId')
        if not origin_id:
            return jsonify({"error": {"exception": "MissingValues",
                           "message": "Missing originId"}, "message": None}), 400

        # Invalidate all other tokens for this users origin (browser, app, etc.)
        invalidate_tokens_by_origin_id(user_id, origin_id)

        # Clean all tokens that are invalidated 10 days before or are expired
        cleanup_expired_sessions()

        return jsonify({"error": None, 'message': 'Logout Success'}), 200

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


# Refresh access_token
@accounts.route("/refresh", methods=['GET'])
@jwt_required(refresh=True)
def handle_refresh_token():
    try:
        # Extract the user ID from the JWT
        user_id = get_jwt_identity()
        account = get_account_by_uuid(user_id)
        token_id = get_jwt()["tokenId"]
        # Get user permissions if assigned
        user = get_user_by_linked_account_uuid(user_id)
        if user:
            additional_claims = {"permissions": user.permissions}
        else:
            additional_claims = {"permissions": "none"}

        isValid = check_token_id_is_active(user_id, token_id)
        if isValid:
            # Check if user exists
            access_token = create_access_token(
                identity=account.public_id, fresh=False, additional_claims=additional_claims)
            return jsonify({"error": None, 'message': 'Refresh Success', 'access_token': access_token}), 200
        else:
            return jsonify({
                "error": {
                    "exception": "TokenExpired",
                    "message": "Your session was invalidated. Please log in again."
                },
                "message": None
            }), 401
    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


# Get User Account
@accounts.route("/me", methods=['GET'])
@jwt_required()
def handle_get_my_account():
    try:
        # Extract the user ID from the JWT
        user_id = get_jwt_identity()
        account = get_account_by_uuid(user_id)

        # Check if user exists
        if account:
            return jsonify({"error": None, 'message': {'username': account.username,
                                                       'timeCreated': account.time_created,
                                                       'linkedUserId': account.linked_user_id
                                                       }}), 200
        else:
            return jsonify({"error": None, 'message': 'User not found'}), 404

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


@accounts.route("/<public_id>", methods=['PATCH'])
@jwt_required()
@roles_required("admin")
def handle_link_user(public_id):
    try:
        # Parse JSON data
        data = request.get_json()

        # Extract and validate username and password
        linked_user_id = data.get('userId')

        # Check if user list is empty
        if not linked_user_id:  # Check if list is empty
            return jsonify({"error": {"exception": "UserNotFound",
                           "message": "Please provide an userId to link account to"}, "message": None}), 400

        return update_link_user_to_account(public_id, linked_user_id)

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


# Get User Account
@accounts.route("/", methods=['GET'])
@jwt_required()
@roles_required("admin")
def handle_get_all_accounts():
    try:
        accounts = get_all_accounts()

        # Check if user list is empty
        if not accounts:  # Check if list is empty
            return jsonify({"error": {"exception": "AccountNotFound",
                           "message": "No accounts were found"}, "message": None}), 404

        # Convert all users to JSON format
        return jsonify({
            "error": None,
            "message": [{
                'publicId': account.public_id,
                'username': account.username,
                'timeCreated': account.time_created,
                'linkedUserId': account.linked_user_id
            } for account in accounts]
        }), 200

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


@accounts.route("/password", methods=['PATCH'])
@jwt_required()
@roles_required("admin", "user")
def handle_change_password_by_user():
    try:
        # Extract the user ID from the JWT
        user_id = get_jwt_identity()
        # Parse JSON data
        data = request.get_json()

        password = data.get('password')
        if not password:
            return jsonify({"error": {"exception": "MissingValues",
                           "message": "Missing Password"}, "message": None}), 400

        # Check if pattern matches
        if not re.match(passwordPattern, password):
            return jsonify({"error": {"exception": "WrongPasswordFormat",
                           "message": "Password must at least be 8 characters long and contain upper and lowercase letters and numbers"}, "message": None}), 400

        # Update the account
        response = update_account_password(user_id, password)
        if response["error"]:
            return jsonify(response), map_sqlstate_to_http_status(response["error"]["pgCode"])
        else:
            return jsonify(response), 200

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


# Change password by admin
@accounts.route("/password/<public_id>", methods=['DELETE'])
@jwt_required()
@roles_required("admin")
def handle_change_password_by_admin(public_id):
    try:
        # Update the account
        response = update_account_password(public_id, "BudeBerkach2025")
        if response["error"]:
            return jsonify(response), map_sqlstate_to_http_status(response["error"]["pgCode"])
        else:
            return jsonify(response), 200

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


# Logout sessions by admin
@accounts.route("/session/terminate", methods=['POST'])
@jwt_required()
@roles_required("admin")
def handle_terminate_session_by_admin():
    try:
        # Parse JSON data
        data = request.get_json()

        account_id = data.get('accountId')
        origin_id = data.get('originId')
        if not origin_id or not account_id:
            return jsonify({"error": {"exception": "MissingValues",
                           "message": "Missing originId, accountId"}, "message": None}), 400

        # Invalidate all other tokens for this users origin (browser, app, etc.)
        invalidate_tokens_by_origin_id(account_id, origin_id)

        return jsonify({"error": None, 'message': 'Logout Success'}), 200

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


# Logout sessions by admin
@accounts.route("/session/terminate/<public_id>", methods=['GET'])
@jwt_required()
@roles_required("admin")
def handle_terminate_all_account_sessions_by_admin(public_id):
    try:
        # Invalidate all other tokens for this user (all browser, app, etc.)
        invalidate_tokens_by_account_id(public_id)

        return jsonify({"error": None, 'message': 'Logout Success'}), 200

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


# Get all Account sessions
@accounts.route("/session", methods=['GET'])
@jwt_required()
@roles_required("admin")
def handle_get_all_account_sessions():
    try:
        sessions = get_all_account_sessions()

        # Check if user list is empty
        if not sessions:  # Check if list is empty
            return jsonify({"error": None, "message": {}}), 200

        # Group sessions by accountId
        grouped_sessions = {}
        for session in sessions:
            account_id = session.account_id
            if account_id not in grouped_sessions:
                grouped_sessions[account_id] = []
            grouped_sessions[account_id].append({
                'tokenId': session.token_id,
                'ipAddress': session.ip_address,
                'device': session.device,
                'browser': session.browser,
                'originId': session.origin_id,
                'timeCreated': session.time_created
            })

        # Convert grouped sessions to JSON format
        return jsonify({
            "error": None,
            "message": grouped_sessions
        }), 200

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


# Link the FCM token to the account
@accounts.route("/notification", methods=['POST'])
@jwt_required()
def handle_link_notification_token_to_session():
    try:
        # Extract the user ID from the JWT
        user_id = get_jwt_identity()
        # Parse JSON data
        data = request.get_json()

        notification_token = data.get('notificationToken')
        origin_id = data.get('originId')
        if not notification_token or not origin_id:
            return jsonify({"error": {"exception": "MissingValues",
                           "message": "Missing notificationToken and originId"}, "message": None}), 400

        # Update the session
        response = update_account_session_notification_token(user_id, origin_id, notification_token)
        return jsonify({
            "error": None,
            'message': 'Notification token linked successfully'
        }), 200

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500
