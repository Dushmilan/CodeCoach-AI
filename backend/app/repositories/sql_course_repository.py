from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.models.course_schemas import Course, Module, Lesson
from app.models.orm import CourseORM, ModuleORM, LessonORM
from app.ports.course_repository import CourseRepository


class SqlCourseRepository(CourseRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _course_to_model(self, orm: CourseORM) -> Course:
        return Course(
            id=orm.id,
            title=orm.title,
            description=orm.description,
            language=orm.language,
            icon=orm.icon,
            order=orm.order,
            modules=[],
        )

    def _module_to_model(self, orm: ModuleORM) -> Module:
        return Module(
            id=orm.id,
            course_id=orm.course_id,
            title=orm.title,
            description=orm.description,
            order=orm.order,
            lessons=[],
        )

    def _lesson_to_model(self, orm: LessonORM) -> Lesson:
        from app.models.course_schemas import LessonType

        return Lesson(
            id=orm.id,
            course_id=orm.course_id,
            module_id=orm.module_id,
            title=orm.title,
            type=LessonType(orm.type) if orm.type else LessonType.THEORY,
            content=orm.content,
            order=orm.order,
            starter_code=orm.starter_code,
            test_cases=orm.test_cases,
            question_id=orm.question_id,
            language=orm.language,
        )

    async def _hydrate_course(self, orm: CourseORM) -> Course:
        course = self._course_to_model(orm)
        module_rows = await self.session.execute(
            select(ModuleORM.id)
            .where(ModuleORM.course_id == orm.id)
            .order_by(ModuleORM.order)
        )
        course.modules = [row[0] for row in module_rows.all()]
        return course

    async def _hydrate_module(self, orm: ModuleORM) -> Module:
        module = self._module_to_model(orm)
        lesson_rows = await self.session.execute(
            select(LessonORM.id)
            .where(LessonORM.module_id == orm.id)
            .order_by(LessonORM.order)
        )
        module.lessons = [row[0] for row in lesson_rows.all()]
        return module

    async def get_all_courses(self) -> List[Course]:
        result = await self.session.execute(select(CourseORM).order_by(CourseORM.order))
        courses = []
        for orm in result.scalars().all():
            courses.append(await self._hydrate_course(orm))
        return courses

    async def get_course_by_id(self, course_id: str) -> Optional[Course]:
        result = await self.session.execute(
            select(CourseORM).where(CourseORM.id == course_id)
        )
        orm = result.scalar_one_or_none()
        return await self._hydrate_course(orm) if orm else None

    async def get_module_by_id(self, module_id: str) -> Optional[Module]:
        result = await self.session.execute(
            select(ModuleORM).where(ModuleORM.id == module_id)
        )
        orm = result.scalar_one_or_none()
        return await self._hydrate_module(orm) if orm else None

    async def get_lesson_by_id(self, lesson_id: str) -> Optional[Lesson]:
        result = await self.session.execute(
            select(LessonORM).where(LessonORM.id == lesson_id)
        )
        orm = result.scalar_one_or_none()
        return self._lesson_to_model(orm) if orm else None

    async def get_lessons_by_module(self, module_id: str) -> List[Lesson]:
        result = await self.session.execute(
            select(LessonORM)
            .where(LessonORM.module_id == module_id)
            .order_by(LessonORM.order)
        )
        return [self._lesson_to_model(row) for row in result.scalars().all()]

    async def get_modules_by_course(self, course_id: str) -> List[Module]:
        result = await self.session.execute(
            select(ModuleORM)
            .where(ModuleORM.course_id == course_id)
            .order_by(ModuleORM.order)
        )
        modules = []
        for orm in result.scalars().all():
            modules.append(await self._hydrate_module(orm))
        return modules
