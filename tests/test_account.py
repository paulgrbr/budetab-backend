import os
import sys
import pytest

# Add to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from app import app
from test_setup import setup, setup_schema

@pytest.fixture
def client():
    # Fixture to create a test client for the Flask app
    app.testing = True
    with app.test_client() as client:
        yield client

def test_register_success(client, setup, setup_schema):
    # Test successful registration
    payload = {"username": "Test_user ", "password": "SecurePassword1"}
    response = client.post('/register', json=payload)

    # Assert the response status code is 201 Created
    assert response.status_code == 201, f"Expected status code 201, but got {response.status_code}"

    # Extract the JSON response
    response_data = response.get_json()

    # Assert the response structure and content
    assert response_data["error"] is None, f"Expected 'error' to be None, but got {response_data['error']}"

    # Assert the username is processed correctly
    assert response_data["message"]["username"] == "test_user", f"Expected username 'test_user', but got {response_data['message']['username']}"


def test_database_connection(client, setup, setup_schema):
    response = client.get('/test-connection')
    # Assert the response status code is 200
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}"