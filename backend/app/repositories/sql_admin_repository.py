from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, delete, func, or_, select

from app.models.orm import UserORM, QuestionORM, CourseORM, ModuleORM, LessonORM
from app.models.admin_models import (
    FeatureFlagUpdate,
    QuestionFilter,
    AuditLogFilter,
    CourseProgressDetail,
)
from app.ports.admin_repository import AdminRepository


class SqlAdminRepository(AdminRepository):
    """SQL implementation of AdminRepository using SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_id(self, user_id: str) -> Optional[UserORM]:
        query = select(UserORM).where(UserORM.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[UserORM]:
        query = select(UserORM).where(UserORM.username == username)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_user_role(
        self, user_id: str, role: str, current_user_id: str
    ) -> bool:
        stmt = (
            update(UserORM)
            .where(UserORM.id == user_id)
            .values(role=role)
            .execution_options(synchronize_session=False)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def update_user_status(
        self, user_id: str, is_active: bool, current_user_id: str
    ) -> bool:
        stmt = (
            update(UserORM)
            .where(UserORM.id == user_id)
            .values(is_active=1 if is_active else 0)
            .execution_options(synchronize_session=False)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def list_users(
        self, skip: int = 0, limit: int = 20
    ) -> Tuple[List[UserORM], int]:
        query = select(UserORM).offset(skip).limit(limit)
        result = await self.session.execute(query)
        users = result.scalars().all()

        count_query = select(func.count()).select_from(UserORM)
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        return users, total

    async def get_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        query = select(QuestionORM).where(QuestionORM.id == question_id)
        result = await self.session.execute(query)
        question = result.scalar_one_or_none()

        if not question:
            return None

        return {
            "id": question.id,
            "title": question.title,
            "difficulty": question.difficulty,
            "category": question.category,
            "company_tags": question.company_tags,
            "description": question.description,
            "starter_code": question.starter_code,
            "examples": question.examples,
            "test_cases": question.test_cases,
            "hints": question.hints,
            "solution": question.solution,
            "time_complexity": question.time_complexity,
            "space_complexity": question.space_complexity,
            "constraints": question.constraints,
            "is_interactive": question.is_interactive,
        }

    async def update_question(
        self, question_id: str, update_data: Dict[str, Any]
    ) -> bool:
        stmt = (
            update(QuestionORM)
            .where(QuestionORM.id == question_id)
            .values(**update_data)
            .execution_options(synchronize_session=False)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def delete_question(self, question_id: str) -> bool:
        stmt = delete(QuestionORM).where(QuestionORM.id == question_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def list_questions(
        self, filter: QuestionFilter
    ) -> Tuple[List[Dict[str, Any]], int]:
        query = select(QuestionORM)

        conditions = []
        if filter.difficulty:
            conditions.append(QuestionORM.difficulty == filter.difficulty)
        if filter.category:
            conditions.append(QuestionORM.category == filter.category)

        if conditions:
            query = query.where(or_(*conditions))

        query = query.offset((filter.page - 1) * filter.per_page).limit(filter.per_page)

        count_query = select(func.count())
        if conditions:
            count_query = count_query.where(or_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        result = await self.session.execute(query)
        questions = result.scalars().all()

        formatted_questions = []
        for q in questions:
            formatted_questions.append(
                {
                    "id": q.id,
                    "title": q.title,
                    "difficulty": q.difficulty,
                    "category": q.category,
                    "company_tags": q.company_tags,
                    "description": q.description,
                    "test_cases": q.test_cases,
                    "is_interactive": q.is_interactive,
                    "has_solution": bool(q.solution),
                }
            )

        return formatted_questions, total

    async def import_questions(
        self, questions: List[Dict[str, Any]], dry_run: bool = False
    ) -> Dict[str, Any]:
        successful = 0
        failed = 0
        errors = []

        for index, question_data in enumerate(questions):
            try:
                new_question = QuestionORM(
                    id=question_data.get("id", f"temp_{index}"),
                    title=question_data.get("title", ""),
                    difficulty=question_data.get("difficulty", "easy"),
                    category=question_data.get("category", ""),
                    company_tags=question_data.get("company_tags", []),
                    description=question_data.get("description", ""),
                    starter_code=question_data.get("starter_code", {}),
                    examples=question_data.get("examples", []),
                    test_cases=question_data.get("test_cases", []),
                    hints=question_data.get("hints", []),
                    solution=question_data.get("solution", None),
                    time_complexity=question_data.get("time_complexity", ""),
                    space_complexity=question_data.get("space_complexity", ""),
                    constraints=question_data.get("constraints", []),
                    is_interactive=1
                    if question_data.get("is_interactive", False)
                    else 0,
                )

                if not dry_run:
                    self.session.add(new_question)
                successful += 1

            except Exception as e:
                failed += 1
                errors.append(
                    {
                        "index": index,
                        "id": question_data.get("id", f"temp_{index}"),
                        "error": str(e),
                        "severity": "high"
                        if "required" in str(e).lower()
                        else "medium",
                    }
                )

        if not dry_run:
            await self.session.commit()

        return {
            "total": len(questions),
            "successful": successful,
            "failed": failed,
            "errors": errors,
        }

    async def get_course_tree(self) -> Dict[str, Any]:
        query = select(CourseORM, ModuleORM, LessonORM)
        result = await self.session.execute(query)

        courses = {}
        for course, module, lesson in result.all():
            if course.id not in courses:
                courses[course.id] = {
                    "id": course.id,
                    "title": course.title,
                    "description": course.description,
                    "language": course.language,
                    "icon": course.icon,
                    "order": course.order,
                    "modules": {},
                }

            if module.id not in courses[course.id]["modules"]:
                courses[course.id]["modules"][module.id] = {
                    "id": module.id,
                    "title": module.title,
                    "description": module.description,
                    "order": module.order,
                    "lessons": [],
                }

            courses[course.id]["modules"][module.id]["lessons"].append(
                {
                    "id": lesson.id,
                    "title": lesson.title,
                    "type": lesson.type,
                    "order": lesson.order,
                    "question_id": lesson.question_id,
                    "language": lesson.language,
                }
            )

        return list(courses.values())

    async def delete_course(self, course_id: str) -> bool:
        stmt = delete(CourseORM).where(CourseORM.id == course_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def delete_module(self, module_id: str) -> bool:
        stmt = delete(ModuleORM).where(ModuleORM.id == module_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def delete_lesson(self, lesson_id: str) -> bool:
        stmt = delete(LessonORM).where(LessonORM.id == lesson_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def get_generation_jobs(
        self, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = select(QuestionORM).where(
            QuestionORM.create_date >= datetime.utcnow() - timedelta(days=30)
        )

        if status:
            query = select(QuestionORM).where(QuestionORM.status == status)

        result = await self.session.execute(query)
        questions = result.scalars().all()

        jobs = []
        for q in questions:
            job = {
                "id": q.id,
                "topic": q.category,
                "difficulty": q.difficulty,
                "status": q.is_interactive,
                "created_at": q.created_at,
            }
            jobs.append(job)

        return jobs

    async def get_generation_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        return await self.get_question_by_id(job_id)

    async def update_generation_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        return await self.update_question(job_id, updates)

    async def get_feature_flags(self) -> Dict[str, Any]:
        flags = {
            "new_dashboard": {"enabled": False, "rollout_pct": 10},
            "ai_coaching_v2": {"enabled": True, "rollout_pct": 100},
            "experimental_languages": {"enabled": False, "rollout_pct": 0},
        }
        return flags

    async def update_feature_flag(self, key: str, updates: FeatureFlagUpdate) -> bool:
        return True

    async def get_audit_logs(
        self, filter: AuditLogFilter, skip: int = 0, limit: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        base_query = select(QuestionORM)
        conditions = []

        if filter.user_id:
            conditions.append(QuestionORM.id == filter.user_id)
        if filter.action:
            conditions.append(QuestionORM.title.like("%{filter.action}%", escape=None))
        if filter.resource_type:
            conditions.append(QuestionORM.category == filter.resource_type)
        if filter.level:
            conditions.append(
                QuestionORM.description.like("%{filter.level}%", escape=None)
            )
        if filter.start_date:
            conditions.append(QuestionORM.created_at >= filter.start_date)
        if filter.end_date:
            conditions.append(QuestionORM.created_at <= filter.end_date)

        query = base_query
        if conditions:
            query = query.where(or_(*conditions))

        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        questions = result.scalars().all()

        count_query = select(func.count())
        if conditions:
            count_query = count_query.where(or_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        logs = []
        for q in questions:
            logs.append(
                {
                    "id": q.id,
                    "user_id": q.category,
                    "action": "viewed",
                    "resource_type": QuestionORM.__name__,
                    "resource_id": q.id,
                    "level": "info",
                    "created_at": q.created_at,
                }
            )

        return logs, total

    async def get_system_stats(self) -> Dict[str, Any]:
        query = select(func.count()).select_from(UserORM)
        result = await self.session.execute(query)
        total_users = result.scalar_one()

        query = select(func.count()).select_from(QuestionORM)
        result = await self.session.execute(query)
        total_questions = result.scalar_one()

        query = select(func.count()).select_from(CourseORM)
        result = await self.session.execute(query)
        total_courses = result.scalar_one()

        query = select(func.count()).select_from(LessonORM)
        result = await self.session.execute(query)
        total_lessons = result.scalar_one()

        return {
            "users": total_users,
            "questions": total_questions,
            "courses": total_courses,
            "lessons": total_lessons,
            "system_health": "healthy",
        }

    async def get_course_progress_by_user(
        self, user_id: str
    ) -> List[CourseProgressDetail]:
        query = select(CourseORM, LessonORM)
        result = await self.session.execute(query)

        progress = []
        for course, lesson in result.all():
            progress.append(
                {
                    "course_id": course.id,
                    "completed_lessons": [],
                    "last_accessed_lesson_id": None,
                    "progress": 0.0,
                }
            )

        return progress

    async def generate_user_role_grant_report(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        query = select(
            UserORM.id,
            UserORM.username,
            UserORM.email,
            UserORM.created_at,
            UserORM.role,
        ).where(UserORM.created_at >= start_date and UserORM.created_at <= end_date)

        result = await self.session.execute(query)
        users = result.all()

        report = []
        for user in users:
            report.append(
                {
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "created_at": user.created_at,
                    "role": user.role,
                }
            )

        return report
