from test_setup import get_mock_JWT_access_token, get_mock_JWT_refresh_token
import os
import sys
import pytest
from test_setup import setup, setup_schema, setup_account_entry, setup_user_entry

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


def test_register_success(client):
    # Test successful registration
    payload = {"username": "Test_user ", "password": "SecurePassword1"}
    response = client.post('/account/register', json=payload)

    # Assert the response status code is 201 Created
    assert response.status_code == 201, f"Expected status code 201, but got {
        response.status_code}"

    # Extract the JSON response
    response_data = response.get_json()

    # Assert the response structure and content
    assert response_data["error"] is None, f"Expected 'error' to be None, but got {
        response_data['error']}"

    # Assert the username is processed correctly
    assert response_data["message"]["username"] == "test_user", f"Expected username 'test_user', but got {
        response_data['message']['username']}"


def test_login_success(client, setup_account_entry):
    # Test successful login
    payload = {"username": "test_user", "password": "Password123"}
    response = client.post('/account/login', json=payload)

    # Assert the response status code is 200 Ok
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"

    # Extract the JSON response
    response_data = response.get_json()

    # Assert the response structure and content
    assert response_data["error"] is None, f"Expected 'error' to be None, but got {
        response_data['error']}"

    # Assert that "access_token" & "refresh_token" exists in the JSON
    assert "access_token" in response_data, "Access token is missing!"
    assert "refresh_token" in response_data, "Refresh token is missing!"

    # non-empty
    assert response_data["access_token"], "Access token is empty!"
    assert response_data["refresh_token"], "Refresh token is empty!"


def test_login_fail(client):
    user = "test_user3"

    # Make successful registration
    payload = {"username": user, "password": "SecretPW1"}
    response = client.post('/account/register', json=payload)

    # Assert the response status code is 201 Created
    assert response.status_code == 201, f"Expected status code 201 when creating account, but got {
        response.status_code}"

    # Test successful login
    payload = {"username": user, "password": "SecretP"}
    response = client.post('/account/login', json=payload)

    # Assert the response status code is 401 Access Denied
    assert response.status_code == 401, f"Expected status code 401, but got {response.status_code}"

    # Extract the JSON response
    response_data = response.get_json()

    # Assert the response structure and content
    assert response_data["error"] is None, f"Expected 'error' to be None, but got {response_data['error']}"

    # Login failed message
    assert response_data["message"] == "Login Failed", "Access token is empty!"


def test_get_my_account_success(client, setup_account_entry):
    access_token = get_mock_JWT_access_token(False)

    # Use access token to GET /account/me
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/account/me', headers=headers)

    # Ensure request is successful
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"
    data = response.get_json()

    # Ensure expected fields exist and are correct
    assert "message" in data, "Missing user data in response"
    assert "username" in data["message"], "Username missing in response"
    assert data["message"]["username"] == "test_user"


def test_link_user_to_account_success(client, setup_account_entry, setup_user_entry):
    # Test successful registration
    access_token = get_mock_JWT_access_token(True)

    # Use access token to GET /user
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "userId": "0becd0ae-fd81-4f54-9685-160eed903b31"
    }

    response = client.patch('/account/573b0bf8-b599-4b49-a307-b241b9e1b99c', json=payload, headers=headers)

    # Assert the response status code is 200 OK
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"

    # Get user to check if it worked
    # Use access token to GET /user/me
    access_token = get_mock_JWT_access_token(False, "573b0bf8-b599-4b49-a307-b241b9e1b99c")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/user/me', headers=headers)

    # Ensure request is successful
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"

    data = response.get_json()
    assert data["message"]["userId"] == "0becd0ae-fd81-4f54-9685-160eed903b31"
