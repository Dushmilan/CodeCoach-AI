import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from app.models.auth_schemas import UserInDB
from app.ports.user_admin_repository import UserAdminRepository

logger = logging.getLogger(__name__)


class FileUserAdminRepository(UserAdminRepository):
    def __init__(self, users_file: str = ""):
        self._users_file = Path(
            users_file
            or str(
                Path(__file__).resolve().parent.parent.parent / "data" / "users.json"
            )
        )

    def _load_users(self) -> List[Dict[str, Any]]:
        if not self._users_file.exists():
            return []
        with open(self._users_file) as f:
            return json.load(f)

    def _save_users(self, users: List[Dict[str, Any]]):
        self._users_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._users_file, "w") as f:
            json.dump(users, f, indent=2)

    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        for u in self._load_users():
            if u.get("id") == user_id:
                return UserInDB(**u)
        return None

    async def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        for u in self._load_users():
            if u.get("username") == username:
                return UserInDB(**u)
        return None

    async def update_user_role(
        self, user_id: str, role: str, current_user_id: str
    ) -> bool:
        users = self._load_users()
        for u in users:
            if u["id"] == user_id:
                if u["id"] == current_user_id:
                    return False
                u["role"] = role
                self._save_users(users)
                return True
        return False

    async def update_user_status(
        self, user_id: str, is_active: bool, current_user_id: str
    ) -> bool:
        users = self._load_users()
        for u in users:
            if u["id"] == user_id:
                if u["id"] == current_user_id:
                    return False
                u["is_active"] = is_active
                self._save_users(users)
                return True
        return False

    async def list_users(
        self, skip: int = 0, limit: int = 20
    ) -> Tuple[List[UserInDB], int]:
        users = self._load_users()
        parsed = [UserInDB(**u) for u in users]
        return parsed[skip : skip + limit], len(parsed)
