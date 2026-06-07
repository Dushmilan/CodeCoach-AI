from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.models.auth_schemas import UserInDB
from app.models.orm import UserORM
from app.ports.user_repository import UserRepository


class SqlUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _orm_to_model(self, orm: UserORM) -> UserInDB:
        return UserInDB(
            id=orm.id,
            username=orm.username,
            email=orm.email,
            hashed_password=orm.hashed_password,
            created_at=orm.created_at,
            is_active=bool(orm.is_active),
            oauth_provider=orm.oauth_provider,
            oauth_id=orm.oauth_id,
        )

    async def get_by_username(self, username: str) -> Optional[UserInDB]:
        result = await self.session.execute(
            select(UserORM).where(UserORM.username == username)
        )
        orm = result.scalar_one_or_none()
        return self._orm_to_model(orm) if orm else None

    async def get_by_email(self, email: str) -> Optional[UserInDB]:
        result = await self.session.execute(
            select(UserORM).where(UserORM.email == email)
        )
        orm = result.scalar_one_or_none()
        return self._orm_to_model(orm) if orm else None

    async def get_by_id(self, user_id: str) -> Optional[UserInDB]:
        result = await self.session.execute(
            select(UserORM).where(UserORM.id == user_id)
        )
        orm = result.scalar_one_or_none()
        return self._orm_to_model(orm) if orm else None

    async def get_by_oauth(
        self, provider: str, oauth_id: str
    ) -> Optional[UserInDB]:
        result = await self.session.execute(
            select(UserORM).where(
                UserORM.oauth_provider == provider,
                UserORM.oauth_id == oauth_id,
            )
        )
        orm = result.scalar_one_or_none()
        return self._orm_to_model(orm) if orm else None

    async def add(self, user: UserInDB) -> None:
        orm = UserORM(
            id=user.id,
            username=user.username,
            email=user.email,
            hashed_password=user.hashed_password,
            created_at=user.created_at,
            is_active=1 if user.is_active else 0,
            oauth_provider=user.oauth_provider,
            oauth_id=user.oauth_id,
        )
        self.session.add(orm)
        await self.session.flush()
