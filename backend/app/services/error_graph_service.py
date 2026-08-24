"""ErrorGraphService - derives the per-user mistake graph from attempt history.

Read-only view over ``submissions``: groups failures by error signature via
the pure rules module and returns them ranked most-recurring first. The
history window is bounded so the derivation cost stays O(recent history).
"""

from app.models.mistake_schemas import ErrorGraphResponse
from app.ports.submission_repository import SubmissionRepository
from app.services.error_graph_rules import derive_error_graph

# Deriving over the full lifetime is unnecessary; recent history carries the
# signal ("what am I still getting wrong lately?"). Bounded for scalability.
MAX_HISTORY_WINDOW = 1000


class ErrorGraphService:
    def __init__(self, repo: SubmissionRepository):
        self.repo = repo

    async def graph(self, *, user_id: str) -> ErrorGraphResponse:
        submissions = await self.repo.list_by_user(user_id, limit=MAX_HISTORY_WINDOW)
        signatures = derive_error_graph(submissions)
        return ErrorGraphResponse(
            signatures=signatures,
            total_signatures=len(signatures),
        )
