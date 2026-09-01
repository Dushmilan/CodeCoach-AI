"""Workspace + chat persistence endpoints (Redis cache, per-user, auth required)."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.auth_deps import get_current_user
from app.api.dependencies import get_workspace_service
from app.models.auth_schemas import UserResponse
from app.models.workspace_schemas import (
    WorkspaceCodePut,
    WorkspaceCodeOut,
    LastVisitedOut,
    ChatHistoryOut,
)
from app.services.workspace_service import WorkspaceService

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(get_current_user)])


@router.put("/code/{question_id}", status_code=204)
async def put_code(
    question_id: str,
    body: WorkspaceCodePut,
    user: UserResponse = Depends(get_current_user),
    svc: WorkspaceService = Depends(get_workspace_service),
):
    await svc.save_code(user.id, question_id, body.language, body.code)
    return None


@router.get("/code/{question_id}", response_model=WorkspaceCodeOut)
async def get_code(
    question_id: str,
    language: str = Query(..., min_length=1, max_length=20),
    user: UserResponse = Depends(get_current_user),
    svc: WorkspaceService = Depends(get_workspace_service),
):
    data = await svc.get_code(user.id, question_id, language)
    try:
        await svc.set_last_visited(user.id, question_id, language)
    except Exception:
        pass
    if data is None:
        return WorkspaceCodeOut(
            code="", language=language, updated_at=None, question_id=question_id
        )
    return WorkspaceCodeOut(
        code=data.get("code", ""),
        language=data.get("language", language),
        updated_at=data.get("updated_at"),
        question_id=question_id,
    )


@router.delete("/code/{question_id}", status_code=204)
async def delete_code(
    question_id: str,
    language: str = Query(..., min_length=1, max_length=20),
    user: UserResponse = Depends(get_current_user),
    svc: WorkspaceService = Depends(get_workspace_service),
):
    await svc.delete_code(user.id, question_id, language)
    return None


@router.get("/last-visited", response_model=Optional[LastVisitedOut])
async def get_last_visited(
    user: UserResponse = Depends(get_current_user),
    svc: WorkspaceService = Depends(get_workspace_service),
):
    data = await svc.get_last_visited(user.id)
    if data is None:
        return None
    return LastVisitedOut(
        question_id=data.get("question_id", ""),
        language=data.get("language"),
        visited_at=data.get("visited_at", ""),
    )


@router.get("/chat/{question_id}", response_model=ChatHistoryOut)
async def get_chat(
    question_id: str,
    user: UserResponse = Depends(get_current_user),
    svc: WorkspaceService = Depends(get_workspace_service),
):
    messages = await svc.get_chat(user.id, question_id)
    return ChatHistoryOut(question_id=question_id, messages=messages)


@router.delete("/chat/{question_id}", status_code=204)
async def delete_chat(
    question_id: str,
    user: UserResponse = Depends(get_current_user),
    svc: WorkspaceService = Depends(get_workspace_service),
):
    await svc.clear_chat(user.id, question_id)
    return None


@router.get("/meta/{question_id}")
async def get_meta(
    question_id: str,
    user: UserResponse = Depends(get_current_user),
    svc: WorkspaceService = Depends(get_workspace_service),
):
    data = await svc.get_meta(user.id, question_id)
    if data is None:
        return {"question_id": question_id, "language": None, "last_opened_at": None}
    return {"question_id": question_id, **data}
