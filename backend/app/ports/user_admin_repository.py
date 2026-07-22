from abc import ABC, abstractmethod
from typing import Optional, List, Tuple

from app.models.auth_schemas import UserInDB


class UserAdminRepository(ABC):
    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]: ...

    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[UserInDB]: ...

    @abstractmethod
    async def update_user_role(
        self, user_id: str, role: str, current_user_id: str
    ) -> bool: ...

    @abstractmethod
    async def update_user_status(
        self, user_id: str, is_active: bool, current_user_id: str
    ) -> bool: ...

    @abstractmethod
    async def list_users(
        self, skip: int = 0, limit: int = 20
    ) -> Tuple[List[UserInDB], int]: ...
