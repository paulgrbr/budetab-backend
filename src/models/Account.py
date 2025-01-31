import uuid
from datetime import datetime

class Account:
    def __init__(self, public_id: uuid, username: str, password_hash: str, time_created: datetime, linked_user_id=uuid):
        self.public_id = public_id
        self.username = username
        self.password_hash = password_hash
        self.time_created = time_created
        self.linked_user_id = linked_user_id