from abc import ABC, abstractmethod
from typing import Optional

from app.models.auth_schemas import UserInDB


class UserRepository(ABC):
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[UserInDB]: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[UserInDB]: ...

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[UserInDB]: ...

    @abstractmethod
    async def add(self, user: UserInDB) -> None: ...
