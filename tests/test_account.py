from test_setup import setup, setup_schema, setup_account_entry, setup_user_entry
import pytest
import sys
import os
from test_setup import get_mock_JWT_access_token, get_mock_JWT_refresh_token
from endpoints.fcm_service import fcm_notify_all_admins, fcm_notify_all_users, fcm_notify_specific_account, fcm_notify_specific_user
import json
from urllib import response

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


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


def test_get_all_accounts_success(client, setup_account_entry):
    access_token = get_mock_JWT_access_token(True)

    # Use access token to GET /account/me
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/account/', headers=headers)

    # Ensure request is successful
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"
    data = response.get_json()

    # Ensure expected fields exist and are correct
    assert "message" in data, "Missing user data in response"
    assert "username" in data["message"][0], "Username missing in response"
    assert data["message"][0]["username"] == "test_user"

    # Ensure right amount of accounts are listed
    assert len(data["message"]) == 3, "Expected amount of accounts doesn't match"


def test_change_password_by_user_success(client, setup_account_entry):
    # Test successful pw change
    access_token = get_mock_JWT_access_token(False)

    # Use access token to PATCH /password
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "password": "NewPassword123"
    }

    response = client.patch('/account/password', headers=headers, json=payload)

    # Assert the response status code is 200 PATCH
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"

    # Extract the JSON response
    response_data = response.get_json()
    # Assert the account update
    assert response_data["message"]["uuid"] == "d0192fdf-56ee-4aab-81e2-36667414c0b1", f"Expected userId to be 'd0192fdf-56ee-4aab-81e2-36667414c0b1', but got {
        response_data['message']}"

    # Test successful login with new password
    payload = {"username": "test_user", "password": "NewPassword123"}
    response = client.post('/account/login', json=payload)

    # Assert the response status code is 200 Ok
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"


def test_reset_password_by_admin_success(client, setup_account_entry):
    # Test failed login with wrong pw
    payload = {"username": "test_user", "password": "BudeBerkach2025"}
    response = client.post('/account/login', json=payload)
    # Assert the response status code is 401 Unauth
    assert response.status_code == 401, f"Expected status code 401, but got {
        response.status_code}"

    # Test successful pw reset by admin
    access_token = get_mock_JWT_access_token(True)

    # Use access token to DELETE password
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.delete('/account/password/d0192fdf-56ee-4aab-81e2-36667414c0b1', headers=headers)

    # Assert the response status code is 200 PATCH
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"

    # Extract the JSON response
    response_data = response.get_json()
    # Assert the account update
    assert response_data["message"]["uuid"] == "d0192fdf-56ee-4aab-81e2-36667414c0b1", f"Expected userId to be 'd0192fdf-56ee-4aab-81e2-36667414c0b1', but got {
        response_data['message']}"

    # Test successful login with new password
    payload = {"username": "test_user", "password": "BudeBerkach2025"}
    response = client.post('/account/login', json=payload)

    # Assert the response status code is 200 Ok
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"


def test_get_all_account_sessions_success(client, setup_account_entry):
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

    access_token = get_mock_JWT_access_token(True)

    # Use access token to GET /account/session
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/account/session', headers=headers)

    # Ensure request is successful
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"
    data = response.get_json()

    # Ensure expected fields exist and are correct
    assert "message" in data, "Missing user data in response"

    # Ensure right amount of accounts are listed
    assert len(data["message"]) == 1, "Expected amount of accounts doesn't match"

    # Ensure right amount of account sessions are listed
    currentAccount = data["message"]["d0192fdf-56ee-4aab-81e2-36667414c0b1"]
    assert len(currentAccount) == 1, "Expected amount of account sessions doesn't match"

    assert "originId" in currentAccount[0], "Missing origin data in response"
    assert "tokenId" in currentAccount[0], "Missing token data in response"
    assert "ipAddress" in currentAccount[0], "Missing metadata in response"
    assert "device" in currentAccount[0], "Missing metadata in response"
    assert "browser" in currentAccount[0], "Missing metadata in response"


def test_terminate_all_accounts_sessions_by_admin_success(client, setup_account_entry):
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

    access_token = get_mock_JWT_access_token(True)

    # Use access token to GET /account/session
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/account/session', headers=headers)

    # Ensure request is successful
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"
    data = response.get_json()

    # Ensure expected fields exist and are correct
    assert "message" in data, "Missing user data in response"

    # Ensure right amount of accounts are listed
    assert len(data["message"]) == 1, "Expected amount of accounts doesn't match"

    # Ensure right amount of account sessions are listed
    currentAccount = data["message"]["d0192fdf-56ee-4aab-81e2-36667414c0b1"]
    assert len(currentAccount) == 1, "Expected amount of account sessions doesn't match"

    assert "originId" in currentAccount[0], "Missing origin data in response"
    assert "tokenId" in currentAccount[0], "Missing token data in response"
    assert "ipAddress" in currentAccount[0], "Missing metadata in response"
    assert "device" in currentAccount[0], "Missing metadata in response"
    assert "browser" in currentAccount[0], "Missing metadata in response"

    # Use access token to POST /account/session/terminate
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/account/session/terminate/d0192fdf-56ee-4aab-81e2-36667414c0b1', headers=headers)

    # Ensure request is successful
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"

    # Use access token to GET /account/session
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/account/session', headers=headers)

    # Ensure request is successful
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"
    data = response.get_json()

    # Ensure expected fields exist and are correct
    assert "message" in data, "Missing user data in response"

    # Ensure right amount of accounts are listed
    assert len(data["message"]) == 0, "Expected amount of accounts doesn't match"


def test_terminate_origin_sessions_by_admin_success(client, setup_account_entry):
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

    access_token = get_mock_JWT_access_token(True)

    # Use access token to GET /account/session
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/account/session', headers=headers)

    # Ensure request is successful
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"
    data = response.get_json()

    # Ensure expected fields exist and are correct
    assert "message" in data, "Missing user data in response"

    # Ensure right amount of accounts are listed
    assert len(data["message"]) == 1, "Expected amount of accounts doesn't match"

    # Ensure right amount of account sessions are listed
    currentAccount = data["message"]["d0192fdf-56ee-4aab-81e2-36667414c0b1"]
    assert len(currentAccount) == 1, "Expected amount of account sessions doesn't match"

    assert "originId" in currentAccount[0], "Missing origin data in response"
    originId = currentAccount[0]["originId"]
    assert "tokenId" in currentAccount[0], "Missing token data in response"
    assert "ipAddress" in currentAccount[0], "Missing metadata in response"
    assert "device" in currentAccount[0], "Missing metadata in response"
    assert "browser" in currentAccount[0], "Missing metadata in response"

    # Use access token to POST /account/session/terminate
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"accountId": "d0192fdf-56ee-4aab-81e2-36667414c0b1", "originId": originId}
    response = client.post('/account/session/terminate', headers=headers, json=payload)

    # Ensure request is successful
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"

    # Use access token to GET /account/session
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/account/session', headers=headers)

    # Ensure request is successful
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"
    data = response.get_json()

    # Ensure expected fields exist and are correct
    assert "message" in data, "Missing user data in response"

    # Ensure right amount of accounts are listed
    assert len(data["message"]) == 0, "Expected amount of accounts doesn't match"


def test_login_invalidates_old_session_fail(client, setup_account_entry):
    for i in range(5):
        # Test successful login
        # Fails because origin id is not set and therefore old sessions are not invalidated
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

    access_token = get_mock_JWT_access_token(True)

    # Use access token to GET /account/session
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/account/session', headers=headers)

    # Ensure request is successful
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"
    data = response.get_json()

    # Ensure expected fields exist and are correct
    assert "message" in data, "Missing user data in response"

    # Ensure right amount of accounts are listed
    assert len(data["message"]) == 1, "Expected amount of accounts doesn't match"

    # Ensure right amount of account sessions are listed
    currentAccount = data["message"]["d0192fdf-56ee-4aab-81e2-36667414c0b1"]
    assert len(currentAccount) == 5, "Expected amount of account sessions doesn't match"


def test_login_invalidates_old_session_success(client, setup_account_entry):
    for i in range(5):
        # Test successful login
        payload = {"username": "test_user", "password": "Password123",
                   "originId": "80f56ef6-a31f-4114-954b-85cbdc1ec783"}
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

    access_token = get_mock_JWT_access_token(True)

    # Use access token to GET /account/session
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/account/session', headers=headers)

    # Ensure request is successful
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"
    data = response.get_json()

    # Ensure expected fields exist and are correct
    assert "message" in data, "Missing user data in response"

    # Ensure right amount of accounts are listed
    assert len(data["message"]) == 1, "Expected amount of accounts doesn't match"

    # Ensure right amount of account sessions are listed
    currentAccount = data["message"]["d0192fdf-56ee-4aab-81e2-36667414c0b1"]
    assert len(currentAccount) == 1, "Expected amount of account sessions doesn't match"

    assert "originId" in currentAccount[0], "Missing origin data in response"
    assert "tokenId" in currentAccount[0], "Missing token data in response"
    assert "ipAddress" in currentAccount[0], "Missing metadata in response"
    assert "device" in currentAccount[0], "Missing metadata in response"
    assert "browser" in currentAccount[0], "Missing metadata in response"


def test_logout_success(client, setup_account_entry):
    # Test successful login
    payload = {"username": "test_user", "password": "Password123", "originId": "80f56ef6-a31f-4114-954b-85cbdc1ec783"}
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

    # Use access token to GET /account/logout
    headers = {"Authorization": f"Bearer {response_data["access_token"]}"}
    payload = {"originId": "80f56ef6-a31f-4114-954b-85cbdc1ec783"}
    response = client.post('/account/logout', headers=headers, json=payload)

    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"

    access_token = get_mock_JWT_access_token(True)

    # Use access token to GET /account/session
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/account/session', headers=headers)

    # Ensure request is successful
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"
    data = response.get_json()

    # Ensure expected fields exist and are correct
    assert "message" in data, "Missing user data in response"

    # Ensure right amount of accounts are listed
    assert len(data["message"]) == 0, "Expected amount of accounts doesn't match"


@pytest.mark.skipif(sys.platform != "darwin", reason="Only run on local dev env and not in CI/CD")
def test_notify_user_success(client, setup_account_entry, setup_user_entry):
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

    payload = {"notificationToken": "fsOWWlojrkaarH6tQrUYZe:APA91bEWYNWlRwdio2200jEP6M5Gl9OYRIyBCw_IIwQ4PaTUhDhvdhWaJPhy6HHJS1tjJYt-6AbkVc2F-Pif5-JbLY0VzS8fKOJXfcVBgXt9Jn5GFhQP57U",
               "originId": response_data["origin_id"]}

    # Use access token to POST /account/notification
    headers = {"Authorization": f"Bearer {response_data["access_token"]}"}
    response = client.post('/account/notification', headers=headers, json=payload)

    # Assert the response status code is 200 Ok
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"

    response = fcm_notify_specific_user(
        "95cebd35-2489-4dbf-b379-a1f901875831",
        "Alles bereit!",
        "Test 1 hat funktioniert",
        sound=True,
        route="/history",
    )
    assert response == 200, "Expected Response Code 200"

    response = fcm_notify_specific_account(
        "d0192fdf-56ee-4aab-81e2-36667414c0b1",
        "Alles bereit!",
        "Test 2 hat funktioniert",
        sound=True,
        route="/history",
    )
    assert response == 200, "Expected Response Code 200"

    # User is not admin and therefore no notification is sent
    response = fcm_notify_all_admins(
        "Alles bereit!",
        "Test 3 hat funktioniert",
        sound=True,
        route="/history",
    )
    assert response == 200, "Expected Response Code 200"

    response = fcm_notify_all_users(
        "Alles bereit!",
        "Test 4 hat funktioniert",
        sound=True,
        route="/history",
    )
    assert response == 200, "Expected Response Code 200"
