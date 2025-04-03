from email import message
import os
import uuid

from database_service.account import get_all_admin_notification_keys, get_all_user_notification_keys, get_one_account_notification_keys, get_one_users_notification_keys
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request as GoogleAuthRequest


# Lade Firebase Service Account
SCOPES = ['https://www.googleapis.com/auth/firebase.messaging']
SERVICE_ACCOUNT_FILE = os.path.abspath('data/fcm/firebase-credentials.json')
PROJECT_ID = 'budetab-app'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES
)


def get_message(title: str, body: str, sound: bool, route: str, key: str):
    if sound:
        message = {
            "message": {
                "token": key,
                "notification": {
                    "title": title,
                    "body": body
                },
                "android": {
                    "notification": {
                        "sound": "default"
                    }
                },
                "apns": {
                    "payload": {
                        "aps": {
                            "sound": "default"
                        }
                    }
                },
                "data": {
                    "route": route
                }
            }
        }
    else:
        message = {
            "message": {
                "token": key,
                "notification": {
                    "title": title,
                    "body": body
                },
                "data": {
                    "route": route
                }
            }
        }
    return message


def get_fcm_access_token():
    auth_req = GoogleAuthRequest()
    credentials.refresh(auth_req)
    return credentials.token


def fcm_notify_specific_user(user_id: uuid, title: str, body: str, sound: bool = False, route: str = "/home"):
    # Get the user's notification key
    notification_keys = get_one_users_notification_keys(user_id)

    # FCM auth
    url = f'https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send'
    access_token = get_fcm_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json; UTF-8'
    }

    try:
        for key in notification_keys:
            if key is None or key == "":
                continue

            message = get_message(title, body, sound, route, key)

            response = requests.post(url, headers=headers, json=message)
        return 200

    except requests.exceptions.RequestException as e:
        print(f"Error sending notification: {e}")
        return response.json(), response.status_code


def fcm_notify_specific_account(account_id: uuid, title: str, body: str, sound: bool = False, route: str = "/home"):
    # Get the user's notification key
    notification_keys = get_one_account_notification_keys(account_id)

    # FCM auth
    url = f'https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send'
    access_token = get_fcm_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json; UTF-8'
    }

    try:
        for key in notification_keys:
            if key is None or key == "":
                continue

            message = get_message(title, body, sound, route, key)

            response = requests.post(url, headers=headers, json=message)
        return 200

    except requests.exceptions.RequestException as e:
        print(f"Error sending notification: {e}")
        return response.json(), response.status_code


def fcm_notify_all_users(title: str, body: str, sound: bool = False, route: str = "/home"):
    # Get all users notification keys
    notification_keys = get_all_user_notification_keys()

    # FCM auth
    url = f'https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send'
    access_token = get_fcm_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json; UTF-8'
    }

    try:
        for key in notification_keys:
            if key is None or key == "":
                continue

            message = get_message(title, body, sound, route, key)

            response = requests.post(url, headers=headers, json=message)
        return 200

    except requests.exceptions.RequestException as e:
        print(f"Error sending notification: {e}")
        return response.json(), response.status_code


def fcm_notify_all_admins(title: str, body: str, sound: bool = False, route: str = "/home"):
    # Get all users notification keys
    notification_keys = get_all_admin_notification_keys()

    # FCM auth
    url = f'https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send'
    access_token = get_fcm_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json; UTF-8'
    }

    try:
        for key in notification_keys:
            if key is None or key == "":
                continue

            message = get_message(title, body, sound, route, key)

            response = requests.post(url, headers=headers, json=message)
        return 200

    except requests.exceptions.RequestException as e:
        print(f"Error sending notification: {e}")
        return response.json(), response.status_code
