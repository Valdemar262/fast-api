from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models import Statement
from app.repositories.base import BaseRepository


class StatementRepository(BaseRepository[Statement]):
    model = Statement

    async def list_for_user(self, user_id: int | None, *, limit: int, offset: int) -> list[Statement]:
        stmt = select(Statement).where(Statement.deleted_at.is_(None)).limit(limit).offset(offset)
        if user_id is not None:
            # noinspection PyTypeChecker
            stmt = stmt.where(Statement.user_id == user_id)

        result = await self.session.scalars(stmt)
        return list(result)

    async def count_for_user(self, user_id: int | None) -> int:
        stmt = select(func.count()).select_from(Statement).where(Statement.deleted_at.is_(None))
        if user_id is not None:
            # noinspection PyTypeChecker
            stmt = stmt.where(Statement.user_id == user_id)
        return await self.session.scalar(stmt) or 0

    async def get_with_relations(self, statement_id: int) -> Statement | None:
        stmt = (
            select(Statement)
            .where(Statement.id == statement_id, Statement.deleted_at.is_(None))
            .options(selectinload(Statement.user), selectinload(Statement.resource))
        )

        statement: Statement | None = await self.session.scalar(stmt)
        return statement

    async def get_active(self, statement_id: int) -> Statement | None:
        stmt =  select(Statement).where(Statement.deleted_at.is_(None)).where(Statement.id == statement_id)
        statement: Statement | None = await self.session.scalar(stmt)
        return statement