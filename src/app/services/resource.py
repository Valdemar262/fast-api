from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.keys import RESOURCE_LIST_PREFIX, resource_key, resource_list_key
from app.core.cache import Cache
from app.exceptions import NotFoundError
from app.models import Resource
from app.repositories.resource import ResourceRepository
from app.schemas import Page, ResourceCreate, ResourceRead, ResourceUpdate


class ResourceService:
    def __init__(self, session: AsyncSession, cache: Cache) -> None:
        self.session = session
        self.cache = cache
        self.resources = ResourceRepository(session)

    async def list(self, *, limit: int, offset: int) -> Page[ResourceRead]:
        key = resource_list_key(limit=limit, offset=offset)

        cached = await self.cache.get(key)
        if cached is not None:
            return Page[ResourceRead].model_validate_json(cached)

        items = await self.resources.list(limit=limit, offset=offset)
        total = await self.resources.count()
        page: Page[ResourceRead] = Page(
            items=[ResourceRead.model_validate(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )
        await self.cache.set(key, page.model_dump_json())
        return page

    async def get(self, resource_id: int) -> Resource:
        resource = await self.resources.get_by_id(resource_id)
        if resource is None:
            raise NotFoundError(f"Resource for ID: {resource_id} not found")
        return resource

    async def create(self, payload: ResourceCreate) -> Resource:
        resource = await self.resources.create(**payload.model_dump())
        await self.session.commit()
        await self._invalidate()
        return resource

    async def update(self, resource_id: int, payload: ResourceUpdate) -> Resource:
        resource = await self.get(resource_id)

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(resource, field, value)

        await self.session.commit()
        await self._invalidate(resource_id)
        return resource

    async def _invalidate(self, resource_id: int | None = None) -> None:
        if resource_id is not None:
            await self.cache.delete(resource_key(resource_id))
        await self.cache.delete_prefix(RESOURCE_LIST_PREFIX)

    async def delete(self, resource_id: int) -> None:
        resource = await self.get(resource_id)
        await self.resources.delete(resource)
        await self.session.commit()
        await self._invalidate(resource_id)

    async def get_read(self, resource_id: int) -> ResourceRead:
        key = resource_key(resource_id)

        cached = await self.cache.get(key)
        if cached is not None:
            return ResourceRead.model_validate_json(cached)

        resource = await self.get(resource_id)
        schema = ResourceRead.model_validate(resource)
        await self.cache.set(key, schema.model_dump_json())
        return schema
