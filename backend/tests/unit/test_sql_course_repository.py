import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def repo(test_db):
    from app.repositories.sql_course_repository import SqlCourseRepository

    return SqlCourseRepository(test_db)


@pytest_asyncio.fixture
async def seeded_db(repo):
    session = repo.session

    from app.models.orm import CourseORM

    session.add(
        CourseORM(
            id="c-1",
            title="Python",
            description="Learn Python",
            language="python",
            icon="python",
            order=1,
        )
    )

    from app.models.orm import ModuleORM

    session.add(
        ModuleORM(
            id="m-1",
            course_id="c-1",
            title="Basics",
            description="Basic concepts",
            order=1,
        )
    )
    session.add(
        ModuleORM(
            id="m-2",
            course_id="c-1",
            title="Advanced",
            description="Advanced topics",
            order=2,
        )
    )

    from app.models.orm import LessonORM

    session.add(
        LessonORM(
            id="l-1",
            course_id="c-1",
            module_id="m-1",
            title="Intro",
            type="theory",
            content="# Intro",
            order=1,
            language="python",
        )
    )
    session.add(
        LessonORM(
            id="l-2",
            course_id="c-1",
            module_id="m-1",
            title="Variables",
            type="theory",
            content="# Variables",
            order=2,
            language="python",
        )
    )
    session.add(
        LessonORM(
            id="l-3",
            course_id="c-1",
            module_id="m-2",
            title="Functions",
            type="exercise",
            content="# Functions",
            order=1,
            language="python",
            question_id="q-1",
        )
    )

    from app.models.orm import QuestionORM

    session.add(
        QuestionORM(
            id="q-1",
            title="Sample Question",
            difficulty="easy",
            category="basics",
            description="A sample question",
        )
    )

    await session.commit()
    return repo


class TestSqlCourseRepository:
    @pytest.mark.asyncio
    async def test_get_all_courses(self, seeded_db):
        courses = await seeded_db.get_all_courses()
        assert len(courses) == 1
        assert courses[0].id == "c-1"
        assert courses[0].title == "Python"

    @pytest.mark.asyncio
    async def test_get_course_by_id_found(self, seeded_db):
        course = await seeded_db.get_course_by_id("c-1")
        assert course is not None
        assert course.title == "Python"
        assert course.language == "python"

    @pytest.mark.asyncio
    async def test_get_course_by_id_not_found(self, seeded_db):
        course = await seeded_db.get_course_by_id("nonexistent")
        assert course is None

    @pytest.mark.asyncio
    async def test_get_module_by_id_found(self, seeded_db):
        module = await seeded_db.get_module_by_id("m-1")
        assert module is not None
        assert module.title == "Basics"
        assert module.course_id == "c-1"

    @pytest.mark.asyncio
    async def test_get_module_by_id_not_found(self, seeded_db):
        module = await seeded_db.get_module_by_id("nonexistent")
        assert module is None

    @pytest.mark.asyncio
    async def test_get_lesson_by_id_found(self, seeded_db):
        lesson = await seeded_db.get_lesson_by_id("l-1")
        assert lesson is not None
        assert lesson.title == "Intro"
        assert lesson.type.value == "theory"
        assert lesson.language == "python"

    @pytest.mark.asyncio
    async def test_get_lesson_by_id_not_found(self, seeded_db):
        lesson = await seeded_db.get_lesson_by_id("nonexistent")
        assert lesson is None

    @pytest.mark.asyncio
    async def test_get_lessons_by_module(self, seeded_db):
        lessons = await seeded_db.get_lessons_by_module("m-1")
        assert len(lessons) == 2
        assert lessons[0].title == "Intro"
        assert lessons[1].title == "Variables"

    @pytest.mark.asyncio
    async def test_get_lessons_by_module_empty(self, seeded_db):
        lessons = await seeded_db.get_lessons_by_module("nonexistent")
        assert lessons == []

    @pytest.mark.asyncio
    async def test_get_modules_by_course(self, seeded_db):
        modules = await seeded_db.get_modules_by_course("c-1")
        assert len(modules) == 2
        assert modules[0].title == "Basics"
        assert modules[1].title == "Advanced"

    @pytest.mark.asyncio
    async def test_get_modules_by_course_empty(self, seeded_db):
        modules = await seeded_db.get_modules_by_course("nonexistent")
        assert modules == []

    @pytest.mark.asyncio
    async def test_course_module_lesson_relationships(self, seeded_db):
        course = await seeded_db.get_course_by_id("c-1")
        assert course is not None

        modules = await seeded_db.get_modules_by_course(course.id)
        assert len(modules) == 2

        m1_lessons = await seeded_db.get_lessons_by_module(modules[0].id)
        assert len(m1_lessons) == 2

        m2_lessons = await seeded_db.get_lessons_by_module(modules[1].id)
        assert len(m2_lessons) == 1
        assert m2_lessons[0].question_id == "q-1"

    @pytest.mark.asyncio
    async def test_lesson_order(self, seeded_db):
        lessons = await seeded_db.get_lessons_by_module("m-1")
        orders = [lesson.order for lesson in lessons]
        assert orders == sorted(orders)

    @pytest.mark.asyncio
    async def test_course_hydrates_module_ids(self, seeded_db):
        course = await seeded_db.get_course_by_id("c-1")
        assert course is not None
        assert course.modules == ["m-1", "m-2"]

    @pytest.mark.asyncio
    async def test_module_hydrates_lesson_ids(self, seeded_db):
        module = await seeded_db.get_module_by_id("m-1")
        assert module is not None
        assert module.lessons == ["l-1", "l-2"]

    @pytest.mark.asyncio
    async def test_get_all_courses_hydrates_modules(self, seeded_db):
        courses = await seeded_db.get_all_courses()
        assert len(courses) == 1
        assert courses[0].modules == ["m-1", "m-2"]

    @pytest.mark.asyncio
    async def test_get_modules_by_course_hydrates_lessons(self, seeded_db):
        modules = await seeded_db.get_modules_by_course("c-1")
        assert len(modules) == 2
        assert modules[0].lessons == ["l-1", "l-2"]
        assert modules[1].lessons == ["l-3"]
