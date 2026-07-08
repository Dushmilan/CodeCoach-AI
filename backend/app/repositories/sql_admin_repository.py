from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, delete, func, or_, select

from app.models.orm import UserORM, QuestionORM, CourseORM, ModuleORM, LessonORM
from app.models.admin_models import (
    QuestionFilter,
    CourseProgressDetail,
)
from app.ports.admin_repository import AdminRepository


class SqlAdminRepository(AdminRepository):
    """SQL implementation of AdminRepository using SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Users ───────────────────────────────────────────

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

    # ── Questions ───────────────────────────────────────

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

        count_query = select(func.count()).select_from(QuestionORM)
        if conditions:
            count_query = count_query.where(or_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        result = await self.session.execute(query)
        questions = result.scalars().all()

        formatted = []
        for q in questions:
            formatted.append(
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

        return formatted, total

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

    # ── Course tree (flat format: {courses, modules, lessons}) ──

    async def get_course_tree(self) -> Dict[str, Any]:
        courses_result = await self.session.execute(
            select(CourseORM).order_by(CourseORM.order)
        )
        courses = []
        for c in courses_result.scalars().all():
            courses.append(
                {
                    "id": c.id,
                    "title": c.title,
                    "description": c.description,
                    "language": c.language,
                    "icon": c.icon,
                    "order": c.order,
                }
            )

        modules_result = await self.session.execute(
            select(ModuleORM).order_by(ModuleORM.order)
        )
        modules = []
        for m in modules_result.scalars().all():
            modules.append(
                {
                    "id": m.id,
                    "course_id": m.course_id,
                    "title": m.title,
                    "description": m.description,
                    "order": m.order,
                }
            )

        lessons_result = await self.session.execute(
            select(LessonORM).order_by(LessonORM.order)
        )
        lessons = []
        for les in lessons_result.scalars().all():
            lessons.append(
                {
                    "id": les.id,
                    "course_id": les.course_id,
                    "module_id": les.module_id,
                    "title": les.title,
                    "type": les.type,
                    "order": les.order,
                    "question_id": les.question_id,
                    "language": les.language,
                }
            )

        return {"courses": courses, "modules": modules, "lessons": lessons}

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

    # ── Curriculum CRUD ─────────────────────────────────

    async def create_course(self, data: Dict[str, Any]) -> Dict[str, Any]:
        orm = CourseORM(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            language=data.get("language", ""),
            icon=data.get("icon", "code"),
            order=data.get("order", 1),
        )
        self.session.add(orm)
        await self.session.commit()
        return {
            "id": orm.id,
            "title": orm.title,
            "description": orm.description,
            "language": orm.language,
            "icon": orm.icon,
            "order": orm.order,
        }

    async def update_course(self, course_id: str, data: Dict[str, Any]) -> bool:
        stmt = (
            update(CourseORM)
            .where(CourseORM.id == course_id)
            .values(**data)
            .execution_options(synchronize_session=False)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def create_module(self, data: Dict[str, Any]) -> Dict[str, Any]:
        orm = ModuleORM(
            id=data["id"],
            course_id=data["course_id"],
            title=data["title"],
            description=data.get("description", ""),
            order=data.get("order", 1),
        )
        self.session.add(orm)
        await self.session.commit()
        return {
            "id": orm.id,
            "course_id": orm.course_id,
            "title": orm.title,
            "description": orm.description,
            "order": orm.order,
        }

    async def update_module(self, module_id: str, data: Dict[str, Any]) -> bool:
        stmt = (
            update(ModuleORM)
            .where(ModuleORM.id == module_id)
            .values(**data)
            .execution_options(synchronize_session=False)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def create_lesson(self, data: Dict[str, Any]) -> Dict[str, Any]:
        from app.models.course_schemas import LessonType

        lesson_type = data.get("type", LessonType.THEORY.value)
        orm = LessonORM(
            id=data["id"],
            course_id=data["course_id"],
            module_id=data["module_id"],
            title=data["title"],
            type=lesson_type,
            content=data.get("content", ""),
            order=data.get("order", 1),
            starter_code=data.get("starter_code"),
            test_cases=data.get("test_cases"),
            question_id=data.get("question_id"),
            language=data.get("language", ""),
        )
        self.session.add(orm)
        await self.session.commit()
        return {
            "id": orm.id,
            "course_id": orm.course_id,
            "module_id": orm.module_id,
            "title": orm.title,
            "type": orm.type,
            "content": orm.content,
            "order": orm.order,
            "language": orm.language,
        }

    async def update_lesson(self, lesson_id: str, data: Dict[str, Any]) -> bool:
        stmt = (
            update(LessonORM)
            .where(LessonORM.id == lesson_id)
            .values(**data)
            .execution_options(synchronize_session=False)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def create_question(self, data: Dict[str, Any]) -> Dict[str, Any]:
        orm = QuestionORM(
            id=data["id"],
            title=data["title"],
            difficulty=data.get("difficulty", "medium"),
            category=data.get("category", ""),
            company_tags=data.get("company_tags", []),
            description=data.get("description", ""),
            starter_code=data.get(
                "starter_code", {"python": "", "javascript": "", "java": ""}
            ),
            examples=data.get("examples", []),
            test_cases=data.get("test_cases", []),
            hints=data.get("hints", []),
            solution=data.get("solution", None),
            time_complexity=data.get("time_complexity", ""),
            space_complexity=data.get("space_complexity", ""),
            constraints=data.get("constraints", []),
            is_interactive=1 if data.get("is_interactive", False) else 0,
        )
        self.session.add(orm)
        await self.session.commit()
        return {
            "id": orm.id,
            "title": orm.title,
            "difficulty": orm.difficulty,
            "category": orm.category,
        }

    # ── Stats ───────────────────────────────────────────

    async def get_system_stats(self) -> Dict[str, Any]:
        users_count = await self.session.execute(
            select(func.count()).select_from(UserORM)
        )
        total_users = users_count.scalar_one()

        questions_count = await self.session.execute(
            select(func.count()).select_from(QuestionORM)
        )
        total_questions = questions_count.scalar_one()

        courses_count = await self.session.execute(
            select(func.count()).select_from(CourseORM)
        )
        total_courses = courses_count.scalar_one()

        lessons_count = await self.session.execute(
            select(func.count()).select_from(LessonORM)
        )
        total_lessons = lessons_count.scalar_one()

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
        return []
