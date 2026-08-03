from typing import Dict, Any, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, delete, select

from app.models.orm import CourseORM, ModuleORM, LessonORM
from app.ports.course_admin_repository import CourseAdminRepository
from app.utils.db import execute_write


class SqlCourseAdminRepository(CourseAdminRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def exists(self, entity_type: str, entity_id: str) -> bool:
        model_map: Dict[str, Type[Any]] = {
            "course": CourseORM,
            "module": ModuleORM,
            "lesson": LessonORM,
        }
        model = model_map.get(entity_type)
        if not model:
            return False
        result = await self.session.execute(
            select(model.id).where(model.id == entity_id).limit(1)
        )
        return result.scalar_one_or_none() is not None

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
        result = await execute_write(self.session, stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def delete_module(self, module_id: str) -> bool:
        stmt = delete(ModuleORM).where(ModuleORM.id == module_id)
        result = await execute_write(self.session, stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def delete_lesson(self, lesson_id: str) -> bool:
        stmt = delete(LessonORM).where(LessonORM.id == lesson_id)
        result = await execute_write(self.session, stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def create_course(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if await self.exists("course", data["id"]):
            raise FileExistsError(f"Course with id '{data['id']}' already exists")
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
        result = await execute_write(self.session, stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def create_module(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not await self.exists("course", data["course_id"]):
            raise FileNotFoundError(f"Course '{data['course_id']}' does not exist")
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
        result = await execute_write(self.session, stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def create_lesson(self, data: Dict[str, Any]) -> Dict[str, Any]:
        from app.models.course_schemas import LessonType

        if not await self.exists("module", data["module_id"]):
            raise FileNotFoundError(f"Module '{data['module_id']}' does not exist")
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
        result = await execute_write(self.session, stmt)
        await self.session.commit()
        return result.rowcount > 0
