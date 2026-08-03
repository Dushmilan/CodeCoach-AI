from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, delete, func, or_, select

from app.models.orm import QuestionORM
from app.models.admin_models import QuestionFilter, QuestionImportResult
from app.ports.question_admin_repository import QuestionAdminRepository
from app.utils.db import execute_write


class SqlQuestionAdminRepository(QuestionAdminRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

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
        result = await execute_write(self.session, stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def delete_question(self, question_id: str) -> bool:
        stmt = delete(QuestionORM).where(QuestionORM.id == question_id)
        result = await execute_write(self.session, stmt)
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
    ) -> QuestionImportResult:
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
        return QuestionImportResult(
            total=len(questions), successful=successful, failed=failed, errors=errors
        )

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
