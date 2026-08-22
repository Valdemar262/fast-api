from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import UserRole
from app.exceptions import BookingConflictError, NotFoundError, PermissionDeniedError
from app.models import Booking, User
from app.repositories.booking import BookingRepository
from app.repositories.resource import ResourceRepository
from app.schemas import BookingCreate, BookingRead, Page


class BookingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.bookings = BookingRepository(session)
        self.resources = ResourceRepository(session)

    async def create(self, payload: BookingCreate, *, user_id: int) -> Booking:
        resource = await self.resources.get_by_id(payload.resource_id)
        if resource is None:
            raise NotFoundError(f"Resource {payload.resource_id} not found")

        has_overlap = await self.bookings.has_overlap(
            resource_id=payload.resource_id,
            start_time=payload.start_time,
            end_time=payload.end_time,
        )

        if has_overlap:
            raise BookingConflictError(f"Resource {payload.resource_id} is already booked for this time range")

        booking = await self.bookings.create(**payload.model_dump(), user_id=user_id)
        await self.session.commit()
        return booking

    async def list_for_resource(self, resource_id: int, *, limit: int, offset: int) -> Page[BookingRead]:
        resource = await self.resources.get_by_id(resource_id)

        if resource is None:
            raise NotFoundError(f"Resource {resource_id} not found")

        total = await self.bookings.count_for_resource(resource_id=resource_id)
        items = await self.bookings.list_for_resource(resource_id=resource_id, limit=limit, offset=offset)

        return Page(
            items=[BookingRead.model_validate(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def delete(self, booking_id: int, actor: User) -> None:
        booking = await self.bookings.get_by_id(booking_id)

        if booking is None:
            raise NotFoundError(f"Booking {booking_id} not found")

        if booking.user_id != actor.id and actor.role != UserRole.ADMIN:
            raise PermissionDeniedError("You can only delete your own bookings")

        await self.bookings.delete(booking)
        await self.session.commit()
