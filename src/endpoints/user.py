import os
from pathlib import Path
from PIL import Image
from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from database_service.sqlstate import map_sqlstate_to_http_status
from database_service.user import create_user, delete_user_by_user_id, get_all_users, get_profile_picture_path_by_user_id, get_user_by_linked_account_uuid, get_user_by_user_id, update_user, update_user_profile_picture_path
from endpoints.jwt_handlers import roles_required
from models.User import User
from werkzeug.utils import secure_filename

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
            is_temporary,
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


# User profile picture
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


# Check if filetype is allowed
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def process_image(file):
    img = Image.open(file)

    # Convert to RGB
    if img.mode in ("RGBA", "P"):  # Handle transparent PNG
        img = img.convert("RGB")

    # Resize if larger than 128x128
    OUTPUT_SIZE = [128, 128]
    if img.size[0] > OUTPUT_SIZE[0] or img.size[1] > OUTPUT_SIZE[1]:
        img = img.resize(OUTPUT_SIZE, Image.LANCZOS)

    return img


@users.route("/profile-picture", methods=["POST"])
@jwt_required()
@roles_required("admin", "user")
def handle_upload_my_profile_picture():
    try:
        # Extract the user ID from the JWT
        public_id = get_jwt_identity()
        user = get_user_by_linked_account_uuid(public_id)

        if "file" not in request.files:
            return jsonify({"error": {"exception": "NoFileError", "message": "No file in request"}, "message": None}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": {"exception": "NoFileError", "message": "No file selected"}, "message": None}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": {"exception": "InvalidFileType",
                                      "message": "Filetype not allowed. Please use .jpg or .png"}, "message": None}), 400

        # Image processing
        filename = str(user.user_id) + ".jpg"
        file_path = os.path.join("data/images/profile_pictures/", filename)

        image = process_image(file)  # Convert to 128x128 JPG
        image.save(file_path, "JPEG", quality=85)

        response = update_user_profile_picture_path(user.user_id, file_path)
        if response["error"]:
            return jsonify(response), map_sqlstate_to_http_status(response["error"]["pgCode"])
        else:
            return jsonify(response), 201

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


@users.route("/profile-picture/<user_id>", methods=["POST"])
@jwt_required()
@roles_required("admin")
def handle_upload_user_profile_picture(user_id):
    try:
        user = get_user_by_user_id(user_id)
        if not user:
            return jsonify({"error": {"exception": "UserNotFound", "message": "UserId is invalid"}, "message": None}), 404

        if "file" not in request.files:
            return jsonify({"error": {"exception": "NoFileError", "message": "No file in request"}, "message": None}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": {"exception": "NoFileError", "message": "No file selected"}, "message": None}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": {"exception": "InvalidFileType",
                                      "message": "Filetype not allowed. Please use .jpg or .png"}, "message": None}), 400

        # Image processing
        filename = str(user_id) + ".jpg"
        file_path = os.path.join("data/images/profile_pictures/", filename)

        image = process_image(file)  # Convert to 128x128 JPG
        image.save(file_path, "JPEG", quality=85)

        response = update_user_profile_picture_path(user_id, file_path)
        if response["error"]:
            return jsonify(response), map_sqlstate_to_http_status(response["error"]["pgCode"])
        else:
            return jsonify(response), 201

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


@users.route("/profile-picture", methods=["GET"])
@jwt_required()
@roles_required("admin", "user")
def handle_get_my_profile_picture():
    try:
        # Extract the user ID from the JWT
        public_id = get_jwt_identity()
        user = get_user_by_linked_account_uuid(public_id)
        relative_db_path = get_profile_picture_path_by_user_id(user.user_id)

        # Check if picture exists
        if relative_db_path:
            current_dir = Path(__file__).resolve().parent
            project_root = current_dir.parent.parent
            file_path = project_root / relative_db_path

            if not os.path.exists(file_path):
                return jsonify({"error": {"exception": "FileNotFound",
                               "message": "File not found"}, "message": None}), 404

            return send_file(file_path, mimetype="image/jpeg")
        else:
            return jsonify({"error": {"exception": "UserNotFound",
                           "message": "No profile picture assigned or user not found"}, 'message': None}), 404

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


@users.route("/profile-picture/<user_id>", methods=["GET"])
@jwt_required()
@roles_required("admin", "user")
def handle_get_user_profile_picture(user_id):
    try:
        relative_db_path = get_profile_picture_path_by_user_id(user_id)

        # Check if picture exists
        if relative_db_path:
            current_dir = Path(__file__).resolve().parent
            project_root = current_dir.parent.parent
            file_path = project_root / relative_db_path

            if not os.path.exists(file_path):
                return jsonify({"error": {"exception": "FileNotFound",
                               "message": "File not found"}, "message": None}), 404

            return send_file(file_path, mimetype="image/jpeg")
        else:
            return jsonify({"error": {"exception": "UserNotFound",
                           "message": "No profile picture assigned or user not found"}, 'message': None}), 404

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


@users.route("/<user_id>", methods=['GET'])
@jwt_required()
@roles_required("admin", "user")
def handle_get_specific_user(user_id):
    try:
        user = get_user_by_user_id(user_id)

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


@users.route("/<user_id>", methods=['PUT'])
@jwt_required()
@roles_required("admin")
def handle_update_user(user_id):
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
        response = update_user(
            user_id,
            first_name,
            last_name,
            is_temporary,
            price_ranking.strip().lower(),
            permissions.strip().lower())
        if response["error"]:
            return jsonify(response), map_sqlstate_to_http_status(response["error"]["pgCode"])
        else:
            return jsonify(response), 200

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500
