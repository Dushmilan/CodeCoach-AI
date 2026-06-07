from sqlalchemy import select, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
import logging

from app.models.schemas import Question, QuestionSummary, Difficulty
from app.models.orm import QuestionORM
from app.ports.question_repository import QuestionRepository

logger = logging.getLogger(__name__)


class SqlQuestionRepository(QuestionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _orm_to_model(self, orm: QuestionORM) -> Question:
        return Question(
            id=orm.id,
            title=orm.title,
            difficulty=Difficulty(orm.difficulty),
            category=orm.category,
            company_tags=orm.company_tags or [],
            description=orm.description,
            starter=orm.starter_code or {"python": "", "javascript": "", "java": ""},
            examples=orm.examples or [],
            test_cases=orm.test_cases or [],
            hints=orm.hints or [],
            solution=orm.solution,
            time_complexity=orm.time_complexity,
            space_complexity=orm.space_complexity,
            constraints=orm.constraints or [],
            is_interactive=bool(orm.is_interactive),
        )

    async def get_all(
        self, difficulty: Optional[Difficulty] = None, category: Optional[str] = None
    ) -> List[Question]:
        stmt = select(QuestionORM)
        if difficulty:
            stmt = stmt.where(QuestionORM.difficulty == difficulty.value)
        if category:
            stmt = stmt.where(QuestionORM.category.ilike(category))
        stmt = stmt.order_by(QuestionORM.title)
        result = await self.session.execute(stmt)
        return [self._orm_to_model(q) for q in result.scalars().all()]

    async def get_by_id(self, question_id: str) -> Optional[Question]:
        result = await self.session.execute(
            select(QuestionORM).where(QuestionORM.id == question_id)
        )
        orm = result.scalar_one_or_none()
        return self._orm_to_model(orm) if orm else None

    async def search(
        self,
        query: str,
        difficulty: Optional[Difficulty] = None,
        category: Optional[str] = None,
    ) -> List[Question]:
        query_param = f"%{query}%"
        stmt = select(QuestionORM).where(
            or_(
                QuestionORM.title.ilike(query_param),
                QuestionORM.description.ilike(query_param),
            )
        )
        if difficulty:
            stmt = stmt.where(QuestionORM.difficulty == difficulty.value)
        if category:
            stmt = stmt.where(QuestionORM.category.ilike(category))
        stmt = stmt.order_by(QuestionORM.title)
        result = await self.session.execute(stmt)
        return [self._orm_to_model(q) for q in result.scalars().all()]

    async def get_categories(self) -> List[str]:
        result = await self.session.execute(
            select(QuestionORM.category).distinct().order_by(QuestionORM.category)
        )
        return [r[0] for r in result.all()]

    async def get_company_tags(self) -> List[str]:
        # JSONB array elements extracted via unnest for PostgreSQL, fallback for SQLite
        dialect = self.session.bind.dialect.name if self.session.bind else "sqlite"
        if dialect == "postgresql":
            result = await self.session.execute(
                text("""
                    SELECT DISTINCT jsonb_array_elements_text(company_tags) as tag
                    FROM questions
                    WHERE company_tags IS NOT NULL AND jsonb_array_length(company_tags) > 0
                """)
            )
        else:
            stmt = select(QuestionORM.company_tags).where(
                QuestionORM.company_tags.isnot(None)
            )
            result = await self.session.execute(stmt)
            tags = set()
            for row in result.all():
                row_tags = row[0]
                if isinstance(row_tags, list):
                    for t in row_tags:
                        tags.add(str(t))
            return sorted(tags)
        return sorted([r[0] for r in result.all()])

    async def add(self, question: Question) -> None:
        orm = QuestionORM(
            id=question.id,
            title=question.title,
            difficulty=question.difficulty.value,
            category=question.category,
            company_tags=question.company_tags,
            description=question.description,
            starter_code=question.starter.model_dump()
            if hasattr(question.starter, "model_dump")
            else question.starter,
            examples=[
                e.model_dump() if hasattr(e, "model_dump") else e
                for e in question.examples
            ],
            test_cases=[
                tc.model_dump() if hasattr(tc, "model_dump") else tc
                for tc in question.test_cases
            ],
            hints=question.hints,
            solution=question.solution,
            time_complexity=question.time_complexity,
            space_complexity=question.space_complexity,
            constraints=question.constraints,
            is_interactive=1 if question.is_interactive else 0,
        )
        self.session.add(orm)
        await self.session.flush()

    async def save_validation_status(
        self, question_id: str, status: Any
    ) -> None:
        pass

    async def get_validation_statuses(self) -> Dict[str, Any]:
        return {}
