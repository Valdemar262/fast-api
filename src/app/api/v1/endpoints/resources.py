from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentUser, ResourceServiceDep, require_role
from app.enums import UserRole
from app.models import Resource
from app.schemas import Page, ResourceCreate, ResourceRead, ResourceUpdate

router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("", response_model=Page[ResourceRead])
async def list_resources(
        service: ResourceServiceDep,
        _: CurrentUser,
        limit: int = Query(default=50, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
) -> Page[ResourceRead]:
    return await service.list(limit=limit, offset=offset)


@router.get("/{resource_id}", response_model=ResourceRead)
async def get_resource(
        resource_id: int,
        service: ResourceServiceDep,
        _: CurrentUser,
) -> Resource:
    return await service.get(resource_id)


@router.post(
    "",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
    response_model=ResourceRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_resource(
        payload: ResourceCreate,
        service: ResourceServiceDep,
) -> Resource:
    return await service.create(payload)


@router.put(
    "/{resource_id}",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
    response_model=ResourceRead,
    status_code=status.HTTP_200_OK,
)
async def update_resource(
        resource_id: int,
        payload: ResourceUpdate,
        service: ResourceServiceDep,
) -> Resource:
    return await service.update(resource_id, payload)


@router.delete(
    "/{resource_id}",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_resource(
        resource_id: int,
        service: ResourceServiceDep,
) -> None:
    return await service.delete(resource_id)
