from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, func, select

from app.models.orm import UserORM
from app.models.auth_schemas import UserInDB
from app.ports.user_admin_repository import UserAdminRepository
from app.utils.db import execute_write


class SqlUserAdminRepository(UserAdminRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        query = select(UserORM).where(UserORM.id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()
        if user is None:
            return None
        return UserInDB(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=bool(user.is_active),
            role=user.role,
            oauth_provider=user.oauth_provider,
            oauth_id=user.oauth_id,
            created_at=str(user.created_at) if user.created_at else None,
            hashed_password=user.hashed_password,
        )

    async def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        query = select(UserORM).where(UserORM.username == username)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()
        if user is None:
            return None
        return UserInDB(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=bool(user.is_active),
            role=user.role,
            oauth_provider=user.oauth_provider,
            oauth_id=user.oauth_id,
            created_at=str(user.created_at) if user.created_at else None,
            hashed_password=user.hashed_password,
        )

    async def update_user_role(
        self, user_id: str, role: str, current_user_id: str
    ) -> bool:
        if user_id == current_user_id:
            return False
        stmt = (
            update(UserORM)
            .where(UserORM.id == user_id)
            .values(role=role)
            .execution_options(synchronize_session=False)
        )
        result = await execute_write(self.session, stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def update_user_status(
        self, user_id: str, is_active: bool, current_user_id: str
    ) -> bool:
        if user_id == current_user_id:
            return False
        stmt = (
            update(UserORM)
            .where(UserORM.id == user_id)
            .values(is_active=1 if is_active else 0)
            .execution_options(synchronize_session=False)
        )
        result = await execute_write(self.session, stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def list_users(
        self, skip: int = 0, limit: int = 20
    ) -> Tuple[List[UserInDB], int]:
        query = select(UserORM).offset(skip).limit(limit)
        result = await self.session.execute(query)
        users = result.scalars().all()

        count_query = select(func.count()).select_from(UserORM)
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        parsed = []
        for u in users:
            parsed.append(
                UserInDB(
                    id=u.id,
                    username=u.username,
                    email=u.email,
                    is_active=bool(u.is_active),
                    role=u.role,
                    oauth_provider=u.oauth_provider,
                    oauth_id=u.oauth_id,
                    created_at=str(u.created_at) if u.created_at else None,
                    hashed_password=u.hashed_password,
                )
            )
        return parsed, total
