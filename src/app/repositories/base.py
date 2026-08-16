from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base


class BaseRepository[ModelT: Base]:
    model: type[ModelT]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, entity_id: int) -> ModelT | None:
        return await self.session.get(self.model, entity_id)

    async def list(self, *, limit: int = 50, offset: int = 0) -> list[ModelT]:
        stmt = select(self.model).limit(limit).offset(offset).order_by(self.model.id)
        result = await self.session.scalars(stmt)
        return list(result)

    async def count(self) -> int:
        stmt = select(func.count()).select_from(self.model)
        return await self.session.scalar(stmt) or 0

    async def create(self, **values: Any) -> ModelT:
        entity = self.model(**values)
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def delete(self, entity: ModelT) -> None:
        await self.session.delete(entity)
        await self.session.flush()
