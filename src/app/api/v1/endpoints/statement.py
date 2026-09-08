from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentUser, StatementServiceDep, require_role
from app.enums import StatusTransitionType, UserRole
from app.models import Statement
from app.schemas import Page, StatementCreate, StatementDetailRead, StatementRead, StatementUpdate

router = APIRouter(prefix="/statements", tags=["statements"])


@router.post(
    "",
    response_model=StatementRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a statement (always starts as a draft)",
    responses={
        401: {"description": "Missing or invalid token"},
        404: {"description": "Resource not found"},
    },
)
async def create_statement(
    payload: StatementCreate,
    service: StatementServiceDep,
    user: CurrentUser,
) -> Statement:
    return await service.create(payload=payload, user_id=user.id)


@router.get(
    "",
    response_model=Page[StatementRead],
    summary="List statements (clients see only their own)",
    responses={
        401: {"description": "Missing or invalid token"},
    },
)
async def list_statements(
    service: StatementServiceDep,
    user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Page[StatementRead]:
    return await service.list_statements(user, limit=limit, offset=offset)


@router.get(
    "/{statement_id}",
    response_model=StatementDetailRead,
    summary="Read one statement with its author and resource",
    responses={
        401: {"description": "Missing or invalid token"},
        403: {"description": "Not the owner and not an admin"},
        404: {"description": "Statement not found"},
    },
)
async def get_statement_by_id(
    statement_id: int,
    service: StatementServiceDep,
    user: CurrentUser,
) -> StatementDetailRead:
    return await service.get_statement_by_id(statement_id, user)


@router.post(
    "/{statement_id}/submit",
    response_model=StatementRead,
    summary="Submit a draft for review",
    responses={
        401: {"description": "Missing or invalid token"},
        403: {"description": "Not allowed for this role"},
        404: {"description": "Statement not found"},
        409: {"description": "Transition not allowed from the current status"},
    },
)
async def submit(
    statement_id: int,
    service: StatementServiceDep,
    user: CurrentUser,
) -> Statement:
    return await service.transition(statement_id, StatusTransitionType.SUBMIT, actor=user)


@router.post(
    "/{statement_id}/approve",
    response_model=StatementRead,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
    summary="Approve a submitted statement",
    responses={
        401: {"description": "Missing or invalid token"},
        403: {"description": "Requires the admin role"},
        404: {"description": "Statement not found"},
        409: {"description": "Statement is not in the submitted state, or has no resource"},
    },
)
async def approve(
    statement_id: int,
    service: StatementServiceDep,
    user: CurrentUser,
) -> Statement:
    return await service.transition(statement_id, StatusTransitionType.APPROVE, actor=user)


@router.post(
    "/{statement_id}/reject",
    response_model=StatementRead,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
    summary="Reject a submitted statement",
    responses={
        401: {"description": "Missing or invalid token"},
        403: {"description": "Requires the admin role"},
        404: {"description": "Statement not found"},
        409: {"description": "Statement is not in the submitted state"},
    },
)
async def reject(
    statement_id: int,
    service: StatementServiceDep,
    user: CurrentUser,
) -> Statement:
    return await service.transition(statement_id, StatusTransitionType.REJECT, actor=user)


@router.put(
    "/{statement_id}",
    response_model=StatementRead,
    status_code=status.HTTP_200_OK,
    summary="Update a statement (title, number, date)",
    responses={
        401: {"description": "Missing or invalid token"},
        403: {"description": "Not the owner and not an admin"},
        404: {"description": "Statement not found"},
    },
)
async def update(
    statement_id: int,
    payload: StatementUpdate,
    service: StatementServiceDep,
    actor: CurrentUser,
) -> Statement:
    return await service.update(statement_id, payload, actor)


@router.delete(
    "/{statement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a statement",
    responses={
        401: {"description": "Missing or invalid token"},
        403: {"description": "Not the owner and not an admin"},
        404: {"description": "Statement not found"},
    },
)
async def delete_statement(
    statement_id: int,
    service: StatementServiceDep,
    actor: CurrentUser,
) -> None:
    return await service.delete(statement_id, actor)
