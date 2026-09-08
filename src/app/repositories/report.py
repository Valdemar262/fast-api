import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import StatementStatus
from app.models import Booking, Resource, Statement, User


class ReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def statements_by_status(
        self, since: datetime.datetime | None
    ) -> dict[StatementStatus, int]:
        stmt = (
            select(Statement.status, func.count().label("total"))
            .where(Statement.deleted_at.is_(None))
            .group_by(Statement.status)
        )
        if since is not None:
            stmt = stmt.where(Statement.created_at >= since)

        result = await self.session.execute(stmt)
        return {row.status: row.total for row in result}

    async def bookings_by_resource(self) -> list[tuple[int, str, int]]:
        stmt = (
            select(Resource.id, Resource.name, func.count(Booking.id).label("bookings_count"))
            .select_from(Resource)
            .outerjoin(Booking, Booking.resource_id == Resource.id)
            .group_by(Resource.id, Resource.name)
            .order_by(func.count(Booking.id).desc(), Resource.id)
        )
        result = await self.session.execute(stmt)
        return [(row.id, row.name, row.bookings_count) for row in result]

    async def user_activity(self) -> list[tuple[int, str, str, int, int]]:
        statements_count = (
            select(func.count())
            .select_from(Statement)
            .where(Statement.user_id == User.id, Statement.deleted_at.is_(None))
            .scalar_subquery()
            .label("statements_count")
        )
        bookings_count = (
            select(func.count())
            .select_from(Booking)
            .where(Booking.user_id == User.id)
            .scalar_subquery()
            .label("bookings_count")
        )
        stmt = select(User.id, User.name, User.email, statements_count, bookings_count).order_by(
            User.id
        )

        result = await self.session.execute(stmt)
        return [
            (row.id, row.name, row.email, row.statements_count, row.bookings_count)
            for row in result
        ]

    async def statements_trend(
        self, since: datetime.datetime | None
    ) -> list[tuple[datetime.date, int]]:
        day = func.date_trunc("day", Statement.created_at).label("day")
        stmt = (
            select(day, func.count().label("total"))
            .where(Statement.deleted_at.is_(None))
            .group_by(day)
            .order_by(day)
        )
        if since is not None:
            stmt = stmt.where(Statement.created_at >= since)

        result = await self.session.execute(stmt)
        return [(row.day.date(), row.total) for row in result]
