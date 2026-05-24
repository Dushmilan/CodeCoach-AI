import json
import os
from typing import Optional
from datetime import datetime

from app.models.auth_schemas import UserInDB
from app.ports.user_repository import UserRepository


class FileUserRepository(UserRepository):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._users: dict[str, UserInDB] = {}
        self._load()

    def _load(self):
        if not os.path.exists(self.file_path):
            return
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            item["created_at"] = datetime.fromisoformat(item["created_at"])
            u = UserInDB(**item)
            self._users[u.id] = u

    def _save(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        data = []
        for u in self._users.values():
            d = u.model_dump()
            d["created_at"] = d["created_at"].isoformat()
            data.append(d)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    async def get_by_username(self, username: str) -> Optional[UserInDB]:
        for u in self._users.values():
            if u.username == username:
                return u
        return None

    async def get_by_email(self, email: str) -> Optional[UserInDB]:
        for u in self._users.values():
            if u.email == email:
                return u
        return None

    async def get_by_id(self, user_id: str) -> Optional[UserInDB]:
        return self._users.get(user_id)

    async def get_by_oauth(
        self, provider: str, oauth_id: str
    ) -> Optional[UserInDB]:
        for u in self._users.values():
            if u.oauth_provider == provider and u.oauth_id == oauth_id:
                return u
        return None

    async def add(self, user: UserInDB) -> None:
        self._users[user.id] = user
        self._save()
