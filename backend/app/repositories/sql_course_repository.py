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
        orms = result.scalars().all()
        if not orms:
            return []
        # Batch fetch module ids for all courses in one query — avoids N+1 (14 roundtrips → 2)
        course_ids = [o.id for o in orms]
        mod_rows = await self.session.execute(
            select(ModuleORM.id, ModuleORM.course_id, ModuleORM.order)
            .where(ModuleORM.course_id.in_(course_ids))
            .order_by(ModuleORM.course_id, ModuleORM.order)
        )
        # Order rows already sorted; group preserving order
        from collections import defaultdict

        mod_map: dict[str, list[str]] = defaultdict(list)
        # Need to preserve order within course; query orders by course_id, order so within each course it's sorted
        for mid, cid, _ in mod_rows.all():
            mod_map[cid].append(mid)
        courses: List[Course] = []
        for orm in orms:
            c = self._course_to_model(orm)
            c.modules = mod_map.get(orm.id, [])
            courses.append(c)
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

    async def get_lesson_summaries_by_module_ids(
        self, module_ids: List[str]
    ) -> List[Lesson]:
        """Batch fetch lessons for course outline — only titles/metadata, no heavy content.

        Single query for all modules (vs N per-module queries) and omits
        `content`/`starter_code`/`test_cases` which bloat payload & latency.
        `Lesson.content` is set to empty string for outline use; full fetch
        via get_lesson_by_id when user opens a lesson.
        """
        if not module_ids:
            return []
        result = await self.session.execute(
            select(
                LessonORM.id,
                LessonORM.course_id,
                LessonORM.module_id,
                LessonORM.title,
                LessonORM.type,
                LessonORM.order,
                LessonORM.question_id,
                LessonORM.language,
            )
            .where(LessonORM.module_id.in_(module_ids))
            .order_by(LessonORM.module_id, LessonORM.order)
        )
        lessons: List[Lesson] = []
        for (
            lid,
            course_id,
            module_id,
            title,
            type_val,
            order,
            question_id,
            language,
        ) in result.all():
            from app.models.course_schemas import LessonType

            lessons.append(
                Lesson(
                    id=lid,
                    course_id=course_id,
                    module_id=module_id,
                    title=title,
                    type=LessonType(type_val) if type_val else LessonType.THEORY,
                    content="",  # outline: fetch full via /lessons/{id}
                    order=order,
                    starter_code=None,
                    test_cases=None,
                    question_id=question_id,
                    language=language,
                )
            )
        return lessons

    async def get_modules_by_course(self, course_id: str) -> List[Module]:
        result = await self.session.execute(
            select(ModuleORM)
            .where(ModuleORM.course_id == course_id)
            .order_by(ModuleORM.order)
        )
        orms = result.scalars().all()
        if not orms:
            return []
        # Batch lesson ids in one query instead of N per-module
        module_ids = [m.id for m in orms]
        lesson_rows = await self.session.execute(
            select(LessonORM.id, LessonORM.module_id, LessonORM.order)
            .where(LessonORM.module_id.in_(module_ids))
            .order_by(LessonORM.module_id, LessonORM.order)
        )
        from collections import defaultdict

        lesson_map: dict[str, list[str]] = defaultdict(list)
        for lid, mid, _ in lesson_rows.all():
            lesson_map[mid].append(lid)
        modules: List[Module] = []
        for orm in orms:
            m = self._module_to_model(orm)
            m.lessons = lesson_map.get(orm.id, [])
            modules.append(m)
        return modules

    async def get_modules_by_course_batch(self, course_ids: List[str]) -> List[Module]:
        if not course_ids:
            return []
        result = await self.session.execute(
            select(ModuleORM)
            .where(ModuleORM.course_id.in_(course_ids))
            .order_by(ModuleORM.course_id, ModuleORM.order)
        )
        orms = result.scalars().all()
        if not orms:
            return []
        module_ids = [m.id for m in orms]
        lesson_rows = await self.session.execute(
            select(LessonORM.id, LessonORM.module_id, LessonORM.order)
            .where(LessonORM.module_id.in_(module_ids))
            .order_by(LessonORM.module_id, LessonORM.order)
        )
        lesson_map = {}
        for lid, mid, _ in lesson_rows.all():
            lesson_map.setdefault(mid, []).append(lid)
        modules = []
        for orm in orms:
            m = self._module_to_model(orm)
            m.lessons = lesson_map.get(orm.id, [])
            modules.append(m)
        return modules
