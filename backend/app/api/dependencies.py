from typing import AsyncGenerator, Optional

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings, Settings
from app.core.database import get_db
from app.ports.question_repository import QuestionRepository
from app.ports.course_repository import CourseRepository
from app.ports.progress_repository import ProgressRepository
from app.ports.admin_repository import AdminRepository
from app.ports.user_admin_repository import UserAdminRepository
from app.ports.question_admin_repository import QuestionAdminRepository
from app.ports.course_admin_repository import CourseAdminRepository
from app.ports.user_repository import UserRepository
from app.ports.usage_repository import UsageRepository
from app.ports.submission_repository import SubmissionRepository
from app.ports.review_repository import ReviewRepository
from app.ports.rescue_repository import RescueRepository
from app.repositories.sql_submission_repository import SqlSubmissionRepository
from app.repositories.sql_review_repository import SqlReviewRepository
from app.repositories.sql_rescue_repository import SqlRescueRepository
from app.repositories.sql_question_repository import SqlQuestionRepository
from app.repositories.sql_course_repository import SqlCourseRepository
from app.repositories.sql_progress_repository import SqlProgressRepository
from app.repositories.sql_user_repository import SqlUserRepository
from app.repositories.sql_admin_repository import SqlAdminRepository
from app.repositories.sql_usage_repository import SqlUsageRepository
from app.services.redis_service import RedisCache
from app.services.usage_service import UsageService
from app.services.rescue_service import RescueService
from app.services.review_service import ReviewService
from app.services.error_graph_service import ErrorGraphService
from app.services.learning_analytics_service import LearningAnalyticsService
from app.services.memory_graph_service import MemoryGraphService
from app.ports.code_executor import CodeExecutor
from app.services.piston_service import PistonService
from app.services.question_bank import QuestionBank


async def get_redis_cache(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> Optional[RedisCache]:
    if settings.REDIS_ENABLED and hasattr(request.app.state, "redis_cache"):
        return request.app.state.redis_cache
    return None


async def get_question_repo(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[QuestionRepository, None]:
    yield SqlQuestionRepository(db)


async def get_course_repo(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[CourseRepository, None]:
    yield SqlCourseRepository(db)


async def get_progress_repo(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[ProgressRepository, None]:
    yield SqlProgressRepository(db)


async def get_user_repo(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[UserRepository, None]:
    yield SqlUserRepository(db)


async def get_usage_repo(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[UsageRepository, None]:
    yield SqlUsageRepository(db)


def get_usage_service(
    usage_repo: UsageRepository = Depends(get_usage_repo),
) -> UsageService:
    return UsageService(repo=usage_repo)


async def get_submission_repo(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[SubmissionRepository, None]:
    yield SqlSubmissionRepository(db)


async def get_rescue_repo(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[RescueRepository, None]:
    yield SqlRescueRepository(db)


def get_rescue_service(
    rescue_repo: RescueRepository = Depends(get_rescue_repo),
) -> RescueService:
    return RescueService(repo=rescue_repo)


async def get_review_repo(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[ReviewRepository, None]:
    yield SqlReviewRepository(db)


def get_review_service(
    review_repo: ReviewRepository = Depends(get_review_repo),
) -> ReviewService:
    return ReviewService(repo=review_repo)


def get_error_graph_service(
    submissions: SubmissionRepository = Depends(get_submission_repo),
) -> ErrorGraphService:
    return ErrorGraphService(repo=submissions)


def get_memory_graph_service(
    review_repo: ReviewRepository = Depends(get_review_repo),
    question_repo: QuestionRepository = Depends(get_question_repo),
    submission_repo: SubmissionRepository = Depends(get_submission_repo),
) -> MemoryGraphService:
    return MemoryGraphService(
        review_repo=review_repo,
        question_repo=question_repo,
        submission_repo=submission_repo,
    )


def get_analytics_service(
    repo: SubmissionRepository = Depends(get_submission_repo),
) -> LearningAnalyticsService:
    return LearningAnalyticsService(repo)


async def get_admin_repo(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[AdminRepository, None]:
    yield SqlAdminRepository(db)


async def get_user_admin_repo(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[UserAdminRepository, None]:
    from app.repositories.sql_user_admin_repository import SqlUserAdminRepository

    yield SqlUserAdminRepository(db)


async def get_question_admin_repo(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[QuestionAdminRepository, None]:
    from app.repositories.sql_question_admin_repository import (
        SqlQuestionAdminRepository,
    )

    yield SqlQuestionAdminRepository(db)


async def get_course_admin_repo(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[CourseAdminRepository, None]:
    from app.repositories.sql_course_admin_repository import (
        SqlCourseAdminRepository,
    )

    yield SqlCourseAdminRepository(db)


def get_executor(
    cache: Optional[RedisCache] = Depends(get_redis_cache),
) -> CodeExecutor:
    return PistonService(cache=cache)


async def get_question_bank(
    question_repo: QuestionRepository = Depends(get_question_repo),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
) -> QuestionBank:
    return QuestionBank(repository=question_repo, cache=cache)
