from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentUser, StatementServiceDep, require_role
from app.enums import StatusTransitionType, UserRole
from app.models import Statement
from app.schemas import Page, StatementCreate, StatementDetailRead, StatementRead, StatementUpdate

router = APIRouter(prefix="/statements", tags=["statements"])


@router.post("", response_model=StatementRead, status_code=status.HTTP_201_CREATED)
async def create_statement(
        payload: StatementCreate,
        service: StatementServiceDep,
        user: CurrentUser,
) -> Statement:
    return await service.create(payload=payload, user_id=user.id)


@router.get("", response_model=Page[StatementRead])
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
)
async def get_statement_by_id(
        statement_id: int,
        service: StatementServiceDep,
        user: CurrentUser,
) -> StatementDetailRead:
    return await service.get_statement_by_id(statement_id, user)


@router.post("/{statement_id}/submit", response_model=StatementRead)
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
)
async def update(
        statement_id: int,
        payload: StatementUpdate,
        service: StatementServiceDep,
) -> Statement:
    return await service.update(statement_id, payload)


@router.delete(
    "/{statement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_statement(
        statement_id: int,
        service: StatementServiceDep,
) -> None:
    return await service.delete(statement_id)
