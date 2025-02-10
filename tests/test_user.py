from email import message
import io
import os
import sys
import pytest
from test_setup import get_mock_JWT_access_token, setup, setup_schema, setup_account_entry, setup_user_entry
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


def test_get_my_user_success(client, setup_account_entry, setup_user_entry):
    access_token = get_mock_JWT_access_token(False)

    # Use access token to GET /user/me
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/user/me', headers=headers)

    # Ensure request is successful
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"
    data = response.get_json()

    # Ensure expected fields exist and are correct
    assert "message" in data, "Missing user data in response"

    assert "userId" in data["message"], "UUID missing in response"
    assert data["message"]["userId"] == "95cebd35-2489-4dbf-b379-a1f901875831"

    assert "firstName" in data["message"], "First Name missing in response"
    assert data["message"]["firstName"] == "Test"

    assert "lastName" in data["message"], "Last Name missing in response"
    assert data["message"]["lastName"] == "User"

    assert "isTemporary" in data["message"], "Is Temporary is missing in response"
    assert data["message"]["isTemporary"] == False

    assert "priceRanking" in data["message"], "Price ranking missing in response"
    assert data["message"]["priceRanking"] == "regular"

    assert "permissions" in data["message"], "Permissions variable is missing in response"
    assert data["message"]["permissions"] == "user"


def test_get_all_users_success(client, setup_account_entry, setup_user_entry):
    access_token = get_mock_JWT_access_token(False)

    # Use access token to GET /user/me
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/user/', headers=headers)

    # Ensure request is successful
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"
    data = response.get_json()

    # Ensure expected fields exist and are correct
    assert "message" in data, "Missing user data in response"

    assert "userId" in data["message"][0], "UUID missing in response"
    assert data["message"][0]["userId"] == "95cebd35-2489-4dbf-b379-a1f901875831"

    assert "firstName" in data["message"][0], "First Name missing in response"
    assert data["message"][0]["firstName"] == "Test"

    assert "lastName" in data["message"][0], "Last Name missing in response"
    assert data["message"][0]["lastName"] == "User"

    assert "isTemporary" in data["message"][0], "Is Temporary is missing in response"
    assert data["message"][0]["isTemporary"] == False

    assert "priceRanking" in data["message"][0], "Price ranking missing in response"
    assert data["message"][0]["priceRanking"] == "regular"

    assert "permissions" in data["message"][0], "Permissions variable is missing in response"
    assert data["message"][0]["permissions"] == "user"

    # Ensure right amount of users are listed
    assert len(data["message"]) == 3, "Expected amount of users doesn't match"


def test_create_user_success(client):
    # Test successful registration
    access_token = get_mock_JWT_access_token(True)

    # Use access token to GET /user
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "firstName": "John",
        "lastName": "Doe",
        "isTemporary": 'false',
        "permissions": "user",
        "priceRanking": "member"
    }
    response = client.post('/user/', json=payload, headers=headers)

    # Assert the response status code is 201 Created
    assert response.status_code == 201, f"Expected status code 201, but got {
        response.status_code}"

    # Extract the JSON response
    response_data = response.get_json()

    # Assert the response structure and content
    assert response_data["error"] is None, f"Expected 'error' to be None, but got {
        response_data['error']}"

    # Assert the firstName is processed correctly
    assert response_data["message"]["firstName"] == "John", f"Expected first name 'John', but got {
        response_data['message']['firstName']}"

    # Assert the lastName is processed correctly
    assert response_data["message"]["lastName"] == "Doe", f"Expected last name 'Doe', but got {
        response_data['message']['lastName']}"


def test_user_permissions_fail(client):
    # Test successful registration
    access_token = get_mock_JWT_access_token(False)  # No admin permissions should deny

    # Use access token to GET /user
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "firstName": "John",
        "lastName": "Doe",
        "isTemporary": 'false',
        "permissions": "user",
        "priceRanking": "member"
    }
    response = client.post('/user/', json=payload, headers=headers)

    # Assert the response status code is Forbidden Created
    assert response.status_code == 403, f"Expected status code 403, but got {
        response.status_code}"

    # Extract the JSON response
    response_data = response.get_json()

    # Assert the Exception is processed correctly
    assert response_data["error"]["exception"] == "InsufficientPermissions", f"Expected Error to be 'InsufficientPermissions', but got {
        response_data['error']['exception']}"


def test_delete_user_success(client, setup_account_entry, setup_user_entry):
    # Test successful registration
    access_token = get_mock_JWT_access_token(True)

    # Use access token to GET /user
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.delete('/user/95cebd35-2489-4dbf-b379-a1f901875831', headers=headers)

    # Assert the response status code is 200 Deleted
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"

    # Extract the JSON response
    response_data = response.get_json()
    # Assert the user is correct
    assert response_data["message"] == "User 95cebd35-2489-4dbf-b379-a1f901875831 deleted successfully", f"Expected deleted user to be '95cebd35-2489-4dbf-b379-a1f901875831', but got {
        response_data['message']}"

    # Check if user is really deleted in db
    response = client.get('/user/', headers=headers)
    data = response.get_json()
    message = data["message"]
    assert len(message) == 2, "Expected amount of users doesn't match"


def calculate_ssim(image1, image2):
    # Resize the retrieved image to match the original image
    image2 = image2.resize(image1.size, Image.LANCZOS)

    image1 = np.array(image1.convert("L"))  # Convert to grayscale
    image2 = np.array(image2.convert("L"))  # Convert to grayscale
    return ssim(image1, image2)


def test_upload_and_get_my_profile_picture(client, setup_account_entry, setup_user_entry):
    # Test profile picture upload
    access_token = get_mock_JWT_access_token(False)
    headers = {"Authorization": f"Bearer {access_token}"}

    # Step 1: Read a real image from disk
    image_path = "tests/fixtures/profile.png"
    assert os.path.exists(image_path), "Test image does not exist!"

    with open(image_path, "rb") as img_file:
        image_data = img_file.read()

    # Step 2: Upload the image
    response = client.post(
        "/user/profile-picture",
        data={"file": (io.BytesIO(image_data), "profile.png")},
        content_type="multipart/form-data",
        headers=headers
    )

    assert response.status_code == 201, f"Expected status code 201, but got {
        response.status_code}"
    assert response.json["message"]["status"] == "Picture uploaded successfully", "Error while parsing message"

    # Step 3: Retrieve the image
    response = client.get("/user/profile-picture", headers=headers)

    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"
    retrieved_img_bytes = io.BytesIO(response.data)

    # Step 4: Compare properties of original & retrieved image
    original_img = Image.open(io.BytesIO(image_data))
    retrieved_img = Image.open(retrieved_img_bytes)

    # Compute Structural Similarity Index (SSIM)
    similarity = calculate_ssim(original_img, retrieved_img)
    assert similarity >= 0.94, f"Images are not visually similar enough! SSIM: {similarity:.4f}"
