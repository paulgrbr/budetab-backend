import os
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required
from database_service.product import create_beverage, create_category, get_all_beverages, get_all_product_categories, get_product_by_product_id, get_product_picture_path_by_product_id, update_product_picture_path
from database_service.sqlstate import map_sqlstate_to_http_status
import re
from models.Product import ProductCategory
from endpoints.jwt_handlers import roles_required
from PIL import Image, ImageChops

products = Blueprint('products', __name__)


# Create Product Category
@products.route("/category", methods=['POST'])
@jwt_required()
@roles_required("admin")
def handle_create_category():
    try:
        # Parse JSON data
        data = request.get_json()

        # Extract and categoryName
        category_name = data.get('categoryName')

        if not category_name:
            return jsonify({"error": {"exception": "MissingValues",
                           "message": "Required values: categoryName"}, "message": None}), 400

        # Create the category
        response = create_category(category_name)
        if response["error"]:
            return jsonify(response), map_sqlstate_to_http_status(response["error"]["pgCode"])
        else:
            return jsonify(response), 201

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


# Get all Product Categories
@products.route("/category", methods=['GET'])
@jwt_required()
@roles_required("admin", "user")
def handle_get_all_categories():
    try:
        categories = get_all_product_categories()

        # Check if category list is empty
        if not categories:  # Check if list is empty
            return jsonify({"error": {"exception": "CategoryNotFound",
                           "message": "No categories were found"}, "message": None}), 404

        # Convert all category to JSON format
        return jsonify({
            "error": None,
            "message": [{"id": category.category_id,
                         "name": category.category_name
                         } for category in categories]
        }), 200

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


# Create Beverage
@products.route("/beverage", methods=['POST'])
@jwt_required()
@roles_required("admin")
def handle_create_beverage():
    try:
        # Parse JSON data
        data = request.get_json()

        # Extract data
        product_name = data.get('productName')
        category_id = data.get('categoryId')
        beverage_size = data.get('beverageSize')
        pricing = data.get('pricing')

        # Check if required fields are present
        if any(val is None for val in [product_name, category_id, beverage_size, pricing]):
            return jsonify({"error": {"exception": "MissingValues",
                                      "message": "Required values: productName, categoryId, beverageSize, pricing"},
                            "message": None}), 400

        # Ensure pricing is a dictionary
        if not isinstance(pricing, dict):
            return jsonify({"error": {"exception": "InvalidPricing",
                                      "message": "Pricing must be an object containing 'normal', 'party', 'bigEvent'"},
                            "message": None}), 400

        # Required keys in pricing
        required_pricing_keys = {"normal", "party", "bigEvent"}

        # Check if pricing contains all required keys
        if not required_pricing_keys.issubset(pricing.keys()):
            return jsonify({"error": {"exception": "MissingPricingKeys",
                                      "message": "Pricing must include 'normal', 'party', and 'bigEvent'"},
                            "message": None}), 400

        # Ensure pricing values are numbers
        if not all(isinstance(pricing[key], (int, float)) for key in required_pricing_keys):
            return jsonify({"error": {"exception": "InvalidPricingValues",
                                      "message": "All pricing values must be numbers"},
                            "message": None}), 400

        # Create the product
        response = create_beverage(product_name, category_id, beverage_size, pricing)
        if response["error"]:
            return jsonify(response), map_sqlstate_to_http_status(response["error"]["pgCode"])
        else:
            return jsonify(response), 201

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


# Get all Beverages
@products.route("/beverage", methods=['GET'])
@jwt_required()
@roles_required("admin", "user")
def handle_get_all_beverages():
    try:
        beverages = get_all_beverages()

        # Check if beverage list is empty
        if not beverages:  # Check if list is empty
            return jsonify({"error": {"exception": "BeveragesNotFound",
                           "message": "No beverages were found"}, "message": None}), 404

        # Group beverages by category_id
        grouped_beverages = {}
        for bev in beverages:
            if bev.category_id not in grouped_beverages:
                grouped_beverages[bev.category_id] = {
                    "categoryId": bev.category_id,
                    "beverages": []
                }

            grouped_beverages[bev.category_id]["beverages"].append({
                "id": bev.product_id,
                "productName": bev.product_name,
                "beverageSize": bev.beverage_size,
                "pricing": bev.pricing
            })

        # Convert dict to list for JSON response
        grouped_beverages_list = list(grouped_beverages.values())

        # Convert to JSON response
        return jsonify({
            "error": None,
            "message": grouped_beverages_list
        }), 200

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


# User profile picture
ALLOWED_EXTENSIONS = {"png"}


# Check if filetype is allowed
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def process_image(file_path, output_size=512):
    img = Image.open(file_path).convert("RGBA")

    # 1. Trim transparent edges
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    # 2. Auto-crop uniform border (using the top-left pixel as border color)
    border_color = img.getpixel((0, 0))
    bg = Image.new(img.mode, img.size, border_color)
    diff = ImageChops.difference(img, bg)
    bbox_border = diff.getbbox()
    if bbox_border:
        img = img.crop(bbox_border)

    # 3. Resize while maintaining aspect ratio (largest dimension = output_size)
    ratio = output_size / max(img.size)
    new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
    img = img.resize(new_size, Image.LANCZOS)

    # 4. Center the image on a 128x128 transparent canvas
    final_img = Image.new("RGBA", (output_size, output_size), (0, 0, 0, 0))
    paste_x = (output_size - new_size[0]) // 2
    paste_y = (output_size - new_size[1]) // 2
    final_img.paste(img, (paste_x, paste_y), img)

    return final_img


@products.route("/picture/<product_id>", methods=["POST"])
@jwt_required()
@roles_required("admin")
def handle_upload_product_picture(product_id):
    try:
        user = get_product_by_product_id(product_id)
        if not user:
            return jsonify({"error": {"exception": "ProductNotFound",
                           "message": "productId is invalid"}, "message": None}), 404

        if "file" not in request.files:
            return jsonify({"error": {"exception": "NoFileError", "message": "No file in request"}, "message": None}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": {"exception": "NoFileError", "message": "No file selected"}, "message": None}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": {"exception": "InvalidFileType",
                                      "message": "Filetype not allowed. Please use .png"}, "message": None}), 400

        # Image processing
        filename = "product_" + str(product_id) + ".png"
        file_path = os.path.join("data/images/product_pictures/", filename)

        image = process_image(file)  # Convert to 128x128 JPG
        image.save(file_path, "PNG", quality=85)

        response = update_product_picture_path(product_id, file_path)
        if response["error"]:
            return jsonify(response), map_sqlstate_to_http_status(response["error"]["pgCode"])
        else:
            return jsonify(response), 201

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500


@products.route("/picture/<product_id>", methods=["GET"])
@jwt_required()
@roles_required("admin", "user")
def handle_get_product_picture(product_id):
    try:
        relative_db_path = get_product_picture_path_by_product_id(product_id)

        # Check if picture exists
        if relative_db_path:
            current_dir = Path(__file__).resolve().parent
            project_root = current_dir.parent.parent
            file_path = project_root / relative_db_path

            if not os.path.exists(file_path):
                return jsonify({"error": {"exception": "FileNotFound",
                               "message": "File not found"}, "message": None}), 404

            return send_file(file_path, mimetype="image/png")
        else:
            return jsonify({"error": {"exception": "ProductNotFound",
                           "message": "No picture assigned to the product"}, 'message': None}), 404

    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        return jsonify({"error": {"exception": "Error", "message": "An unexpected error occurred"}, "message": None}), 500
