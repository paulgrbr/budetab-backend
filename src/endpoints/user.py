from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from database_service.sqlstate import map_sqlstate_to_http_status
from database_service.user import create_user, delete_user_by_user_id, get_all_users, get_user_by_linked_account_uuid
from endpoints.jwt_handlers import roles_required
from models.User import User

users = Blueprint('users', __name__)

# Get Users assigned user profile


@users.route("/me", methods=['GET'])
@jwt_required()
@roles_required("admin", "user")
def handle_get_my_user():
    try:
        # Extract the user ID from the JWT
        user_id = get_jwt_identity()
        user = get_user_by_linked_account_uuid(user_id)

        # Check if user exists
        if user:
            return jsonify({"error": None, 'message': {"userId": user.user_id,
                                                       "firstName": user.first_name,
                                                       "lastName": user.last_name,
                                                       "isTemporary": user.is_temporary,
                                                       "priceRanking": user.price_ranking,
                                                       "permissions": user.permissions
                                                       }}), 200
        else:
            return jsonify({"error": {"exception": "UserNotFound",
                           "message": "User not found or not assigned"}, 'message': None}), 404

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


@users.route("/", methods=['POST'])
@jwt_required()
@roles_required("admin")
def handle_create_user():
    try:
        # Parse JSON data
        data = request.get_json()

        # Extract and validate username and password
        first_name = data.get('firstName')
        last_name = data.get('lastName')
        is_temporary = data.get('isTemporary')
        price_ranking = data.get('priceRanking')
        permissions = data.get('permissions')

        if any(val is None for val in [first_name, last_name, is_temporary, price_ranking, permissions]):
            return jsonify({"error": {"exception": "MissingValues",
                           "message": "Required values: firstName, lastName, isTemporary, priceRanking, permissions"}, "message": None}), 400

        # Create the user
        response = create_user(
            first_name,
            last_name,
            bool(is_temporary),
            price_ranking.strip().lower(),
            permissions.strip().lower())
        if response["error"]:
            return jsonify(response), map_sqlstate_to_http_status(response["error"]["pgCode"])
        else:
            return jsonify(response), 201

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


@users.route("/", methods=['GET'])
@jwt_required()
@roles_required("admin", "user")
def handle_get_all_users():
    try:
        users = get_all_users()

        # Check if user list is empty
        if not users:  # Check if list is empty
            return jsonify({"error": {"exception": "UserNotFound",
                           "message": "No users were found"}, "message": None}), 404

        # Convert all users to JSON format
        return jsonify({
            "error": None,
            "message": [{"userId": user.user_id,
                         "firstName": user.first_name,
                         "lastName": user.last_name,
                         "isTemporary": user.is_temporary,
                         "priceRanking": user.price_ranking,
                         "permissions": user.permissions
                         } for user in users]
        }), 200

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


@users.route("/<user_id>", methods=['DELETE'])
@jwt_required()
@roles_required("admin")
def handle_delete_user(user_id):
    try:
        # Check if user list is empty
        if not user_id:  # Check if list is empty
            return jsonify({"error": {"exception": "UserNotFound",
                           "message": "Please provide an userId"}, "message": None}), 400

        return delete_user_by_user_id(user_id)

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500
