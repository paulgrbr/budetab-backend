import os
import sys
import pytest
from test_setup import setup, setup_schema, setup_account_entry

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


def test_database_connection_success(client):
    response = client.get('/account/test-connection')
    # Assert the response status code is 200
    assert response.status_code == 200, f"Expected status code 200, but got {
        response.status_code}"


def test_token_refresh_success(client, setup_account_entry):
    # Make successful login for refresh token
    payload = {"username": "test_user", "password": "Password123"}
    response = client.post('/account/login', json=payload)

    # Assert the response status code is 200 Ok
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}"
    data = response.get_json()

    refresh_token = data["refresh_token"]

    # Use refresh token to GET /account/refresh
    headers = {"Authorization": f"Bearer {refresh_token}"}
    response = client.get('/account/refresh', headers=headers)

    # Ensure request is successful
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}"
    data = response.get_json()

    # Ensure the response contains a new access token
    assert "access_token" in data, "Response does not contain an access token"
