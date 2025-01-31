import bcrypt
from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from database_service.account import create_account, get_pg_version, get_accounts_by_username, get_my_account
from database_service.sqlstate import map_sqlstate_to_http_status
import re
from models import Account

accounts = Blueprint('accounts', __name__)

# RegEx patterns
usernamePattern = r"^[a-z0-9_]+$"
passwordPattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?!.*\s).{8,}$"

# Register user route
@accounts.route("/register", methods=['POST'])
def register():
    try:
        # Parse JSON data
        data = request.get_json()
        
        # Extract and validate username and password
        username = data.get('username').strip().lower()
        password = data.get('password')
        if not username or not password:
            return jsonify({"error": {"exception": "MissingValues", "message":"Missing username or password"}, "message": None}), 400

        # Check if pattern matches
        if not re.match(usernamePattern, username):
            return jsonify({"error": {"exception": "WrongUsernameFormat", "message":"Username contains invalid characters"}, "message": None}), 400
        if not re.match(passwordPattern, password):
            return jsonify({"error": {"exception": "WrongPasswordFormat", "message":"Password must at least be 8 characters long and contain upper and lowercase letters and numbers"}, "message": None}), 400

        # Create the account
        response = create_account(username, password)
        if response["error"]:
            return jsonify(response), map_sqlstate_to_http_status(response["error"]["pgCode"])
        else:
            return jsonify(response), 201
    
    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message":"An unexpected error occurred"}, "message": None}), 500

# Test connection to db
@accounts.route("/test-connection", methods=['GET'])
def connection_is_alive():
    return jsonify(get_pg_version()), 200


# Account login route
@accounts.route("/login", methods=['POST'])
def login():
    try:
        # Parse JSON data
        data = request.get_json()
        
        # Extract and validate username and password
        username = data.get('username').strip().lower()
        password = data.get('password')
        if not username or not password:
            return jsonify({"error": {"exception": "MissingValues", "message":"Missing username or password"}, "message": None}), 400

        accounts = get_accounts_by_username(username)

        if accounts:
            account = accounts[0]
        else:
            account = None

        if account and bcrypt.checkpw(password.encode("utf-8"), account.password_hash):
            access_token = create_access_token(identity=account.public_id, fresh=True)
            refresh_token = create_refresh_token(identity=account.public_id)
            return jsonify({"error": None, 'message': 'Login Success', 'access_token': access_token, 'refresh_token': refresh_token}), 200
        else:
            return jsonify({"error": None, 'message': 'Login Failed'}), 401
        
    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message":"An unexpected error occurred"}, "message": None}), 500
    

# Test connection to db
@accounts.route("/refresh", methods=['GET'])
@jwt_required(refresh=True)
def refresh_token():
    try:
        # Extract the user ID from the JWT
        user_id = get_jwt_identity()
        account = get_my_account(user_id)

        # Check if user exists
        access_token = create_access_token(identity=account.public_id, fresh=False)
        return jsonify({"error": None, 'message': 'Refresh Success', 'access_token': access_token}), 200
         
    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message":"An unexpected error occurred"}, "message": None}), 500
    

# Refresh access_token
@accounts.route("/me", methods=['GET'])
@jwt_required()
def get_me_account():
    try:
        # Extract the user ID from the JWT
        user_id = get_jwt_identity()
        account = get_my_account(user_id)

        # Check if user exists
        if account:
            return jsonify({"error": None, 'message': { 'username': account.username,
                                                        'time_created': account.time_created,
                                                        'linked_user_id': account.linked_user_id
                                                       }}), 200
        else:
            return jsonify({"error": None, 'message': 'User not found'}), 404
         
    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message":"An unexpected error occurred"}, "message": None}), 500
    
