from typing import AsyncGenerator, Optional
from pathlib import Path

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings, Settings
from app.core.database import get_db
from app.ports.question_repository import QuestionRepository
from app.ports.course_repository import CourseRepository
from app.ports.progress_repository import ProgressRepository
from app.ports.admin_repository import AdminRepository
from app.ports.user_repository import UserRepository
from app.repositories.sql_question_repository import SqlQuestionRepository
from app.repositories.sql_course_repository import SqlCourseRepository
from app.repositories.sql_progress_repository import SqlProgressRepository
from app.repositories.sql_user_repository import SqlUserRepository
from app.repositories.sql_admin_repository import SqlAdminRepository
from app.repositories.file_admin_repository import FileAdminRepository
from app.repositories.file_question_repository import FileQuestionRepository
from app.repositories.file_course_repository import FileCourseRepository
from app.repositories.file_progress_repository import FileProgressRepository
from app.repositories.file_user_repository import FileUserRepository
from app.services.redis_service import RedisCache

BASE_DIR = Path(__file__).resolve().parent.parent.parent


async def get_redis_cache(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> Optional[RedisCache]:
    if settings.REDIS_ENABLED and hasattr(request.app.state, "redis_cache"):
        return request.app.state.redis_cache
    return None


async def get_question_repo(
    db: Optional[AsyncSession] = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AsyncGenerator[QuestionRepository, None]:
    if settings.USE_DATABASE:
        yield SqlQuestionRepository(db)
    else:
        yield FileQuestionRepository(
            str(BASE_DIR / "questions" / "sample_questions.json")
        )


async def get_course_repo(
    db: Optional[AsyncSession] = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AsyncGenerator[CourseRepository, None]:
    if settings.USE_DATABASE:
        yield SqlCourseRepository(db)
    else:
        yield FileCourseRepository(courses_dir=str(BASE_DIR / "data" / "courses"))


async def get_progress_repo(
    db: Optional[AsyncSession] = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AsyncGenerator[ProgressRepository, None]:
    if settings.USE_DATABASE:
        yield SqlProgressRepository(db)
    else:
        yield FileProgressRepository(
            file_path=str(BASE_DIR / "data" / "user_progress.json")
        )


async def get_user_repo(
    db: Optional[AsyncSession] = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AsyncGenerator[UserRepository, None]:
    if settings.USE_DATABASE:
        yield SqlUserRepository(db)
    else:
        yield FileUserRepository(file_path=str(BASE_DIR / "data" / "users.json"))


async def get_admin_repo(
    db: Optional[AsyncSession] = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AsyncGenerator[AdminRepository, None]:
    if settings.USE_DATABASE:
        yield SqlAdminRepository(db)
    else:
        yield FileAdminRepository()
