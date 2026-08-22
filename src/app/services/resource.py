from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError
from app.models import Resource
from app.repositories.resource import ResourceRepository
from app.schemas import Page, ResourceCreate, ResourceRead, ResourceUpdate


class ResourceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.resources = ResourceRepository(session)

    async def list(self, *, limit: int, offset: int) -> Page[ResourceRead]:
        items = await self.resources.list(limit=limit, offset=offset)
        total = await self.resources.count()

        return Page[ResourceRead](
            items=[ResourceRead.model_validate(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get(self, resource_id: int) -> Resource:
        resource = await self.resources.get_by_id(resource_id)
        if resource is None:
            raise NotFoundError(f"Resource {resource_id} not found")
        return resource

    async def create(self, payload: ResourceCreate) -> Resource:
        resource = await self.resources.create(**payload.model_dump())
        await self.session.commit()
        return resource

    async def update(self, resource_id: int, payload: ResourceUpdate) -> Resource:
        resource = await self.get(resource_id)

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(resource, field, value)

        await self.session.commit()
        return resource

    async def delete(self, resource_id: int) -> None:
        resource = await self.get(resource_id)
        await self.resources.delete(resource)
        await self.session.commit()
