from fastapi import APIRouter, Depends, Query, status

from app.api.deps import BookingServiceDep, CurrentUser, ResourceServiceDep, require_role
from app.enums import UserRole
from app.models import Resource
from app.schemas import BookingRead, Page, ResourceCreate, ResourceRead, ResourceUpdate

router = APIRouter(prefix="/resources", tags=["resources"])


@router.get(
    "",
    response_model=Page[ResourceRead],
    summary="List resources",
    responses={401: {"description": "Missing or invalid token"}},
)
async def list_resources(
    service: ResourceServiceDep,
    _: CurrentUser,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Page[ResourceRead]:
    return await service.list(limit=limit, offset=offset)


@router.get(
    "/{resource_id}",
    response_model=ResourceRead,
    summary="Read one resource",
    responses={401: {"description": "Missing or invalid token"}, 404: {"description": "Not found"}},
)
async def get_resource(
    resource_id: int,
    service: ResourceServiceDep,
    _: CurrentUser,
) -> ResourceRead:
    return await service.get_read(resource_id)


@router.post(
    "",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
    response_model=ResourceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a resource",
    responses={
        401: {"description": "Missing or invalid token"},
        403: {"description": "Requires the admin role"},
    },
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
    summary="Update a resource",
    responses={
        401: {"description": "Missing or invalid token"},
        403: {"description": "Requires the admin role"},
        404: {"description": "Resource not found"},
    },
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
    summary="Delete a resource",
    responses={
        401: {"description": "Missing or invalid token"},
        403: {"description": "Requires the admin role"},
        404: {"description": "Resource not found"},
    },
)
async def delete_resource(
    resource_id: int,
    service: ResourceServiceDep,
) -> None:
    return await service.delete(resource_id)


@router.get(
    "/{resource_id}/bookings",
    response_model=Page[BookingRead],
    summary="List bookings of a resource, earliest first",
    responses={
        401: {"description": "Missing or invalid token"},
        404: {"description": "Resource not found"},
    },
)
async def get_bookings(
    resource_id: int,
    service: BookingServiceDep,
    _: CurrentUser,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Page[BookingRead]:
    return await service.list_for_resource(resource_id, limit=limit, offset=offset)
