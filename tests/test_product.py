import io
import os
import sys
import pytest
from test_setup import get_mock_JWT_access_token, setup, setup_schema, setup_account_entry, setup_user_entry, setup_product_entry
from PIL import Image
import numpy as np
from skimage.metrics import structural_similarity as ssim

# Add to the Python path
sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../src')))

from app import app  # noqa


@pytest.fixture
def client():
    # Fixture to create a test client for the Flask app
    app.testing = True
    with app.test_client() as client:
        yield client


def test_create_product_category_success(client):
    # Test successful create category
    access_token = get_mock_JWT_access_token(True)

    # Use access token to POST /product/category
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "categoryName": "Bier"
    }
    response = client.post('/product/category', json=payload, headers=headers)

    # Assert the response status code is 201 Created
    assert response.status_code == 201, f"Expected status code 201, but got {
        response.status_code}"

    # Extract the JSON response
    response_data = response.get_json()

    # Assert the response structure and content
    assert response_data["error"] is None, f"Expected 'error' to be None, but got {
        response_data['error']}"

    # Assert the categoryName is processed correctly
    assert response_data["message"]["categoryName"] == "Bier", f"Expected categoryName to be 'Bier', but got {
        response_data['message']['categoryName']}"


def test_get_all_product_categories_success(client, setup_product_entry):
    access_token = get_mock_JWT_access_token(False)

    # Use access token to GET /product/category
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/product/category', headers=headers)

    # Ensure request is successful
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"
    data = response.get_json()

    # Ensure expected fields exist and are correct
    assert "message" in data, "Missing category data in response"

    assert "id" in data["message"][0], "Id missing in response"
    assert data["message"][0]["id"] == 1

    assert "name" in data["message"][0], "Name missing in response"
    assert data["message"][0]["name"] == "Bier"

    # Ensure right amount of categories are listed
    assert len(data["message"]) == 3, "Expected amount of categories doesn't match"


def test_create_beverage_success(client, setup_product_entry):
    # Test successful creation of beverage
    access_token = get_mock_JWT_access_token(True)

    # Use access token to POST /product/beverage
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "productName": "Gold Ochsen Original",
        "categoryId": 1,
        "beverageSize": 0.5,
        "pricing": {
            "normal": 2.0,
            "party": 2.5,
            "bigEvent": 3.5
        }
    }
    response = client.post('/product/beverage', json=payload, headers=headers)

    # Assert the response status code is 201 Created
    assert response.status_code == 201, f"Expected status code 201, but got {
        response.status_code}"

    # Extract the JSON response
    response_data = response.get_json()

    # Assert the response structure and content
    assert response_data["error"] is None, f"Expected 'error' to be None, but got {
        response_data['error']}"

    # Assert the categoryName is processed correctly
    assert response_data["message"]["status"] == "Beverage added successfully", f"Expected 'Beverage added successfully', but got {
        response_data['message']['status']}"

    product_id = response_data["message"]["productId"]

    # Use access token to GET /beverage
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/product/beverage', headers=headers)

    # Ensure request is successful
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"
    data = response.get_json()

    # Ensure expected fields exist and are correct
    assert "message" in data, "Missing category data in response"

    category_ids = [category["categoryId"] for category in data["message"]]
    assert 1 in category_ids, "Category ID 1 is missing from the response"

    beverages = [cat["beverages"] for cat in data["message"] if cat["categoryId"] == 1][0]
    current_beverage = beverages[0]

    assert "id" in current_beverage, "Id missing in response"
    assert current_beverage["id"] == product_id, f"Expected id to be {product_id} but got {current_beverage["id"]}"

    assert "beverageSize" in current_beverage, "beverageSize missing in response"
    assert current_beverage["beverageSize"] == 0.5, f"Expected beverageSize to be 0.5 but got {
        current_beverage["beverageSize"]}"

    assert "productName" in current_beverage, "productName missing in response"
    assert current_beverage["productName"] == "Gold Ochsen Original", f"Expected productName to be Gold Ochsen Original but got {
        current_beverage["productName"]}"

    assert "pricing" in current_beverage, "pricing missing in response"
    assert current_beverage["pricing"]["normal"] == 2.0, f"Expected normal price to be 2.0 but got {
        current_beverage["pricing"]["normal"]}"

    assert current_beverage["pricing"]["party"] == 2.5, f"Expected party price to be 2.5 but got {
        current_beverage["pricing"]["party"]}"

    assert current_beverage["pricing"]["bigEvent"] == 3.5, f"Expected bigEvent price to be 3.5 but got {
        current_beverage["pricing"]["bigEvent"]}"

    # Ensure right amount of products are listed
    assert len(beverages) == 1, "Expected amount of beverages for categoryId 1 doesn't match"


def test_get_all_beverages_success(client, setup_product_entry):
    # Test successful registration
    access_token = get_mock_JWT_access_token(False)

    # Use access token to GET /product/beverage
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/product/beverage', headers=headers)

    # Assert the response status code is 200 OK
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"

    # Extract the JSON response
    data = response.get_json()

    # Assert the response structure and content
    assert data["error"] is None, f"Expected 'error' to be None, but got {
        data['error']}"

    # Ensure expected fields exist and are correct
    assert "message" in data, "Missing category data in response"

    # Ensure right amount of categories are listed
    assert len(data["message"]) == 2, "Expected amount of categories doesn't match"

    category_ids = [category["categoryId"] for category in data["message"]]
    assert 2 in category_ids, "Category ID 2 is missing from the response"

    beverages = [cat["beverages"] for cat in data["message"] if cat["categoryId"] == 2][0]
    current_beverage = beverages[0]

    assert "id" in current_beverage, "Id missing in response"

    assert "beverageSize" in current_beverage, "beverageSize missing in response"
    assert current_beverage["beverageSize"] == 0.5, f"Expected beverageSize to be 0.5 but got {
        current_beverage["beverageSize"]}"

    assert "productName" in current_beverage, "productName missing in response"
    assert current_beverage["productName"] == "Paulaner Spezi", f"Expected productName to be Paulaner Spezi but got {
        current_beverage["productName"]}"

    assert "pricing" in current_beverage, "pricing missing in response"
    assert current_beverage["pricing"]["normal"] == 1.5, f"Expected normal price to be 2.0 but got {
        current_beverage["pricing"]["normal"]}"

    assert current_beverage["pricing"]["party"] == 2.0, f"Expected party price to be 2.5 but got {
        current_beverage["pricing"]["party"]}"

    assert current_beverage["pricing"]["bigEvent"] == 3.0, f"Expected bigEvent price to be 3.0 but got {
        current_beverage["pricing"]["bigEvent"]}"

    # Ensure right amount of products are listed
    assert len(beverages) == 2, "Expected amount of beverages for categoryId 2 doesn't match"


def calculate_ssim(image1, image2):
    # Resize the retrieved image to match the original image
    image2 = image2.resize(image1.size, Image.LANCZOS)

    image1 = np.array(image1.convert("L"))  # Convert to grayscale
    image2 = np.array(image2.convert("L"))  # Convert to grayscale
    return ssim(image1, image2)


def test_upload_and_get_product_picture_by_admin_success(
        client, setup_account_entry, setup_user_entry, setup_product_entry):
    # Test profile picture upload
    access_token = get_mock_JWT_access_token(True)
    headers = {"Authorization": f"Bearer {access_token}"}

    # Step 1: Read a real image from disk
    image_path = "tests/fixtures/picture_without_background.png"
    assert os.path.exists(image_path), "Test image does not exist!"

    with open(image_path, "rb") as img_file:
        image_data = img_file.read()

    # Step 2: Upload the image
    response = client.post(
        "/product/picture/3",
        data={"file": (io.BytesIO(image_data), "picture_without_background.png")},
        content_type="multipart/form-data",
        headers=headers
    )

    assert response.status_code == 201, f"Expected status code 201, but got {
        response.status_code}"
    assert response.json["message"]["status"] == "Picture uploaded successfully", "Error while parsing message"

    # Step 3: Retrieve the image
    response = client.get("/product/picture/3", headers=headers)

    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"
    retrieved_img_bytes = io.BytesIO(response.data)

    # Step 4: Compare properties of original & retrieved image
    original_img = Image.open(io.BytesIO(image_data))
    retrieved_img = Image.open(retrieved_img_bytes)

    # Compute Structural Similarity Index (SSIM)
    similarity = calculate_ssim(original_img, retrieved_img)
    assert similarity >= 0.65, f"Images are not visually similar enough! SSIM: {similarity:.4f}"


def test_remove_background_picture_by_admin_success(client):
    # Test profile picture upload
    access_token = get_mock_JWT_access_token(True)
    headers = {"Authorization": f"Bearer {access_token}"}

    # Step 1: Read a real image from disk
    image_path = "tests/fixtures/picture_with_background.jpg"
    assert os.path.exists(image_path), "Test image does not exist!"

    with open(image_path, "rb") as img_file:
        image_data = img_file.read()

    # Step 2: Upload the image
    response = client.post(
        "/misc/remove-background/",
        data={"file": (io.BytesIO(image_data), "picture_without_background.png")},
        content_type="multipart/form-data",
        headers=headers
    )

    assert response.status_code == 200, f"Expected status code 201, but got {
        response.status_code}"

    retrieved_img_bytes = io.BytesIO(response.data)

    # Step 3: Read a reference image from disk
    image_path = "tests/fixtures/picture_with_background_removed.png"
    assert os.path.exists(image_path), "Reference image does not exist!"

    with open(image_path, "rb") as img_file:
        image_data = img_file.read()

    # Step 4: Compare properties of original & retrieved image
    reference_image = Image.open(io.BytesIO(image_data))
    retrieved_img = Image.open(retrieved_img_bytes)

    # Compute Structural Similarity Index (SSIM)
    similarity = calculate_ssim(reference_image, retrieved_img)
    assert similarity >= 1.0, f"Images are not visually similar enough! SSIM: {similarity:.4f}"


def test_update_beverage_success(client, setup_product_entry):
    # Test successful update of beverage
    access_token = get_mock_JWT_access_token(True)

    # Use access token to PUT /product/beverage
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "productName": "Paulaner Spezi",
        "categoryId": 1,
        "beverageSize": 0.33,
        "pricing": {
            "normal": 4.0,
            "party": 4.5,
            "bigEvent": 5.5
        }
    }
    response = client.put('/product/beverage/1', json=payload, headers=headers)

    # Assert the response status code is 200 OK
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"

    # Extract the JSON response
    response_data = response.get_json()

    # Assert the response structure and content
    assert response_data["error"] is None, f"Expected 'error' to be None, but got {
        response_data['error']}"

    # Assert the categoryName is processed correctly
    assert response_data["message"]["status"] == "Beverage updated successfully", f"Expected 'Beverage updated successfully', but got {
        response_data['message']['status']}"

    # Check if changes applied
    response = client.get('/product/beverage', headers=headers)

    # Assert the response status code is 200 OK
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"

    # Extract the JSON response
    data = response.get_json()

    # Assert the response structure and content
    assert data["error"] is None, f"Expected 'error' to be None, but got {
        data['error']}"

    # Ensure expected fields exist and are correct
    assert "message" in data, "Missing category data in response"

    # Ensure right amount of categories are listed
    assert len(data["message"]) == 3, "Expected amount of categories doesn't match"

    category_ids = [category["categoryId"] for category in data["message"]]
    assert 1 in category_ids, "Category ID 1 is missing from the response"

    beverages = [cat["beverages"] for cat in data["message"] if cat["categoryId"] == 1][0]
    current_beverage = beverages[0]

    assert "id" in current_beverage, "Id missing in response"

    assert "beverageSize" in current_beverage, "beverageSize missing in response"
    assert current_beverage["beverageSize"] == 0.33, f"Expected beverageSize to be 0.33 but got {
        current_beverage["beverageSize"]}"

    assert "productName" in current_beverage, "productName missing in response"
    assert current_beverage["productName"] == "Paulaner Spezi", f"Expected productName to be Paulaner Spezi but got {
        current_beverage["productName"]}"

    assert "pricing" in current_beverage, "pricing missing in response"
    assert current_beverage["pricing"]["normal"] == 4.0, f"Expected normal price to be 4.0 but got {
        current_beverage["pricing"]["normal"]}"

    assert current_beverage["pricing"]["party"] == 4.5, f"Expected party price to be 4.5 but got {
        current_beverage["pricing"]["party"]}"

    assert current_beverage["pricing"]["bigEvent"] == 5.5, f"Expected bigEvent price to be 5.5 but got {
        current_beverage["pricing"]["bigEvent"]}"

    # Ensure right amount of products are listed
    assert len(beverages) == 1, "Expected amount of beverages for categoryId 1 doesn't match"


def test_delete_product_success(client, setup_product_entry):
    # Test successful registration
    access_token = get_mock_JWT_access_token(True)

    # Use access token to GET /user
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.delete('/product/1', headers=headers)

    # Assert the response status code is 200 Deleted
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"

    # Extract the JSON response
    response_data = response.get_json()
    # Assert the user is correct
    assert response_data["message"] == "Product 1 deleted successfully", f"Product 1 deleted successfully', but got {
        response_data['message']}"

    # Check if changes applied
    response = client.get('/product/beverage', headers=headers)

    # Extract the JSON response
    data = response.get_json()

    # Get Alkoholfrei Category
    beverages = [cat["beverages"] for cat in data["message"] if cat["categoryId"] == 2][0]

    # Ensure right amount of products are listed (2 before, 1 after)
    assert len(beverages) == 1, "Expected amount of beverages for categoryId 2 doesn't match"
