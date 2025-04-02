from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required
from endpoints.jwt_handlers import roles_required
from rembg import remove
from io import BytesIO

misc = Blueprint('misc', __name__)

# User profile picture
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


# Check if filetype is allowed
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@misc.route("/remove-background/", methods=["POST"])
@jwt_required()
@roles_required("admin")
def handle_remove_picture_background():
    try:
        if "file" not in request.files:
            return jsonify({"error": {"exception": "NoFileError", "message": "No file in request"}, "message": None}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": {"exception": "NoFileError", "message": "No file selected"}, "message": None}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": {"exception": "InvalidFileType",
                                      "message": "Filetype not allowed. Please use .jpg, .png or .webp"}, "message": None}), 400

        # Remove the background
        input_bytes = file.read()
        output_bytes = remove(input_bytes)

        # Return the result as a PNG image
        output_io = BytesIO(output_bytes)
        output_io.seek(0)
        return send_file(output_io, mimetype="image/png")

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500
