from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentUser, UserServiceDep, require_role
from app.enums import UserRole
from app.models import User
from app.schemas import Page, RoleUpdate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "",
    response_model=Page[UserRead],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
    summary="List users",
    responses={
        401: {"description": "Missing or invalid token"},
        403: {"description": "Requires the admin role"},
    },
)
async def list_users(
    service: UserServiceDep,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Page[UserRead]:
    return await service.list_users(limit=limit, offset=offset)


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Update your own profile",
    responses={
        401: {"description": "Missing or invalid token"},
    },
)
async def update_user(payload: UserUpdate, service: UserServiceDep, actor: CurrentUser) -> User:
    return await service.update(actor, payload)


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Read a profile (your own, or any as an admin)",
    responses={
        401: {"description": "Missing or invalid token"},
        403: {"description": "Not your profile and not an admin"},
        404: {"description": "User not found"},
    },
)
async def get_user(
    user_id: int,
    service: UserServiceDep,
    actor: CurrentUser,
) -> UserRead:
    return await service.get_profile(user_id, actor)


@router.patch(
    "/{user_id}/role",
    response_model=UserRead,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
    summary="Change a user's role",
    responses={
        401: {"description": "Missing or invalid token"},
        403: {"description": "Requires the admin role, or would demote the last admin"},
        404: {"description": "User not found"},
    },
)
async def update_user_role(
    user_id: int,
    payload: RoleUpdate,
    service: UserServiceDep,
) -> User:
    return await service.update_role(user_id, payload)


@router.delete(
    "/{user_id}",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user (never yourself)",
    responses={
        401: {"description": "Missing or invalid token"},
        403: {"description": "Requires the admin role, or is your own account"},
        404: {"description": "User not found"},
    },
)
async def delete_user(
    user_id: int,
    service: UserServiceDep,
    actor: CurrentUser,
) -> None:
    return await service.delete(user_id, actor)
