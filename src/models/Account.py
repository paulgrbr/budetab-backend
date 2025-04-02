import uuid
from datetime import datetime


class Account:
    def __init__(self, public_id: uuid, username: str, password_hash: str, time_created: datetime, linked_user_id=uuid):
        self.public_id = public_id
        self.username = username
        self.password_hash = password_hash
        self.time_created = time_created
        self.linked_user_id = linked_user_id


class AccountSession:
    def __init__(
        self,
        token_id: uuid,
        account_id: uuid,
        ip_address: str,
        device: str,
        browser: str,
        origin_id: uuid,
        time_created: datetime = None,
    ):
        self.token_id = token_id
        self.account_id = account_id
        self.ip_address = ip_address
        self.device = device
        self.browser = browser
        self.origin_id = origin_id
        self.time_created = time_created
