from abc import ABC, abstractmethod
from typing import List, Optional, Sequence

from app.models.auth_schemas import UserInDB


class UserRepository(ABC):
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[UserInDB]: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[UserInDB]: ...

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[UserInDB]: ...

    @abstractmethod
    async def list_by_ids(self, user_ids: Sequence[str]) -> List[UserInDB]:
        """Batch user lookup in a single query (no N+1). ..."""

    @abstractmethod
    async def get_by_oauth(
        self, provider: str, oauth_id: str
    ) -> Optional[UserInDB]: ...

    @abstractmethod
    async def add(self, user: UserInDB) -> None: ...
