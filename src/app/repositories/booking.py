from datetime import datetime

from sqlalchemy import func, select

from app.models.booking import Booking
from app.repositories.base import BaseRepository


class BookingRepository(BaseRepository[Booking]):
    model = Booking

    async def has_overlap(self, *, resource_id: int, start_time: datetime, end_time: datetime) -> bool:
        stmt = (
            select(Booking.id)
            .where(
                Booking.resource_id == resource_id,
                Booking.start_time < end_time,
                Booking.end_time > start_time,
            )
            .limit(1)
        )

        return await self.session.scalar(stmt) is not None

    async def count_for_resource(self, resource_id: int) -> int:
        stmt = select(func.count()).select_from(Booking).where(Booking.resource_id == resource_id)

        return await self.session.scalar(stmt) or 0

    async def list_for_resource(self, resource_id: int, *, limit: int, offset: int) -> list[Booking]:
        stmt = (
            select(Booking)
            .where(Booking.resource_id == resource_id)
            .order_by(Booking.start_time)
            .limit(limit)
            .offset(offset)
        )

        return list(await self.session.scalars(stmt))