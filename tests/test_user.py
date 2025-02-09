from email import message
import os
import sys
import pytest
from test_setup import get_mock_JWT_access_token, setup, setup_schema, setup_account_entry, setup_user_entry

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
    assert len(message) == 2
