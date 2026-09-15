"""HierarchyService — admin tree over professors, courses, classrooms.

Issue #159 Task 6. Read-only aggregation for ``GET /api/admin/hierarchy``.
Composes existing ports only (never touches a SQL session):

- professors come from ``UserAdminRepository.list_users`` (role filter here,
  since the port has no role query);
- owned rooms from ``ClassroomRepository.list_owned_by_professor``;
- courses resolve from the owned rooms' ``course_id`` values (the Course
  schema carries no owner, so ownership flows through classrooms);
- lesson counts from ``CourseRepository`` module/lesson reads;
- TA names from ``list_classroom_ta_ids`` + user lookup (TAs are staff, so
  the student-only roster read cannot serve this);
- student counts + avg completion from ``ClassAnalyticsService`` (the
  same optimal-path aggregates the instructor views use, with the room's
  real per-course lesson count as the denominator — never a hardcoded
  constant, so completion can never exceed 100%).

Tree shape matches the Task 6 brief exactly::

    {"professors": [{"id", "username",
                     "courses": [{"id", "title", "lessons"}],
                     "classrooms": [{"id", "name", "invite_code",
                                     "tas", "students", "avg_completion"}]}]}
"""

from app.models.orm import ClassroomORM
from app.ports.classroom_repository import ClassroomRepository
from app.ports.course_repository import CourseRepository
from app.ports.user_admin_repository import UserAdminRepository
from app.services.class_analytics_service import ClassAnalyticsService

# list_users pages through the whole user table; large enough that an admin
# tree build stays a handful of queries on realistic tenants.
_USER_PAGE_SIZE = 500


class HierarchyService:
    def __init__(
        self,
        *,
        users: UserAdminRepository,
        classrooms: ClassroomRepository,
        courses: CourseRepository,
        analytics: ClassAnalyticsService,
    ):
        self._users = users
        self._classrooms = classrooms
        self._courses = courses
        self._analytics = analytics

    async def admin_tree(self) -> dict:
        """Assemble the full admin → professors → courses/classrooms tree."""
        professors = [u for u in await self._all_users() if u.role == "professor"]
        professors.sort(key=lambda u: u.username)
        tree = []
        for prof in professors:
            rooms = await self._classrooms.list_owned_by_professor(prof.id)
            course_ids = list(dict.fromkeys(room.course_id for room in rooms))
            lessons_by_course = {
                course_id: await self._lesson_count(course_id)
                for course_id in course_ids
            }
            course_entries = []
            for course_id in course_ids:
                entry = await self._course_entry(
                    course_id, lessons_by_course.get(course_id, 0)
                )
                if entry is not None:
                    course_entries.append(entry)
            room_entries = [
                await self._room_entry(room, lessons_by_course.get(room.course_id, 0))
                for room in rooms
            ]
            tree.append(
                {
                    "id": prof.id,
                    "username": prof.username,
                    "courses": course_entries,
                    "classrooms": room_entries,
                }
            )
        return {"professors": tree}

    async def _all_users(self) -> list:
        """Drain the paginated user listing (the port has no role query)."""
        users = []
        skip = 0
        while True:
            page, _ = await self._users.list_users(skip=skip, limit=_USER_PAGE_SIZE)
            users.extend(page)
            if len(page) < _USER_PAGE_SIZE:
                break
            skip += len(page)
        return users

    async def _lesson_count(self, course_id: str) -> int:
        """Real per-course lesson count backing both the tree and the average."""
        modules = await self._courses.get_modules_by_course(course_id)
        lessons = await self._courses.get_lesson_summaries_by_module_ids(
            [m.id for m in modules]
        )
        return len(lessons)

    async def _course_entry(self, course_id: str, lesson_count: int) -> dict | None:
        course = await self._courses.get_course_by_id(course_id)
        if course is None:
            return None
        return {"id": course.id, "title": course.title, "lessons": lesson_count}

    async def _room_entry(self, room: ClassroomORM, total_lessons: int) -> dict:
        student_ids = await self._classrooms.list_classroom_student_ids(room.id)
        _, overview = await self._analytics.classroom_overview(
            room.id,
            total_lessons=total_lessons,
            classrooms=self._classrooms,
        )
        ta_ids = await self._classrooms.list_classroom_ta_ids(room.id)
        ta_names = []
        for ta_id in ta_ids:
            user = await self._users.get_user_by_id(ta_id)
            if user is not None:
                ta_names.append(user.username)
        return {
            "id": room.id,
            "name": room.name,
            "invite_code": room.invite_code,
            "tas": ta_names,
            "students": len(student_ids),
            "avg_completion": overview.avg_completion,
        }
