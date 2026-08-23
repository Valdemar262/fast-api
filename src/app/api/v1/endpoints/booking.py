from fastapi import APIRouter, status

from app.api.deps import BookingServiceDep, CurrentUser
from app.models import Booking
from app.schemas import BookingCreate, BookingRead

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post(
    "",
    response_model=BookingRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_booking(
        payload: BookingCreate,
        service: BookingServiceDep,
        user: CurrentUser,
) -> Booking:
    return await service.create(payload, user_id=user.id)

@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(
        booking_id: int,
        service: BookingServiceDep,
        user: CurrentUser,
) -> None:
    return await service.delete(booking_id, actor=user)
