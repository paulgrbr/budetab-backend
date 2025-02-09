import uuid
from datetime import datetime


class User:
    def __init__(self, user_id: uuid, first_name: str, last_name: str, time_created: datetime,
                 is_temporary: bool, price_ranking: str, permissions: str):
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.time_created = time_created
        self.is_temporary = is_temporary
        self.price_ranking = price_ranking
        self.permissions = permissions
