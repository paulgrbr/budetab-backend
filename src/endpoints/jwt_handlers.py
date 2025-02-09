from functools import wraps
from flask import jsonify
from flask_jwt_extended import JWTManager, get_jwt, jwt_required

jwt = JWTManager()  # Create a JWTManager instance (initialize later)

# Handle missing or invalid JWT
@jwt.unauthorized_loader
def custom_unauthorized_response(error):
    return jsonify({
        "error": {
            "exception": "Unauthorized",
            "message": "Missing or invalid JWT token."
        },
        "message": None
    }), 401

# Handle invalid tokens (bad signature)
@jwt.invalid_token_loader
def invalid_token_callback(reason):
    return jsonify({
        "error": {
            "exception": "InvalidToken",
            "message": "Signature verification failed"
        }
    }), 401

# Handle expired tokens
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        "error": {
            "exception": "TokenExpired",
            "message": "Your session has expired. Please log in again."
        },
        "message": None
    }), 401

# Handle user permissions
def roles_required(*required_roles):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get("permissions")

            if user_role not in required_roles:
                return jsonify({"error": {"exception": "InsufficientPermissions", "message":"You do not have the required permissions for this"}}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator