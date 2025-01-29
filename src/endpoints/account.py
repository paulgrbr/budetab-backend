from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from database_service.account import create_account, get_pg_version
from database_service.sqlstate import map_sqlstate_to_http_status
import re

accounts = Blueprint('accounts', __name__)

# RegEx patterns
usernamePattern = r"^[a-z0-9_]+$"
passwordPattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?!.*\s).+$"

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
            return jsonify({"error": {"exception": "WrongPasswordFormat", "message":"Password must at least contain upper and lowercase letter and number"}, "message": None}), 400

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