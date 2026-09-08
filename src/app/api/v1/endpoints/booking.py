from fastapi import APIRouter, status

from app.api.deps import BookingServiceDep, CurrentUser
from app.models import Booking
from app.schemas import BookingCreate, BookingRead

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post(
    "",
    response_model=BookingRead,
    status_code=status.HTTP_201_CREATED,
    summary="Book a resource; the owner is taken from the token",
    responses={
        401: {"description": "Missing or invalid token"},
        404: {"description": "Resource not found"},
        409: {"description": "The resource is already booked for that time range"},
    },
)
async def create_booking(
    payload: BookingCreate,
    service: BookingServiceDep,
    user: CurrentUser,
) -> Booking:
    return await service.create(payload, user_id=user.id)


@router.delete(
    "/{booking_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a booking (own, or any as an admin)",
    responses={
        401: {"description": "Missing or invalid token"},
        403: {"description": "Not the owner and not an admin"},
        404: {"description": "Booking not found"},
    },
)
async def delete_booking(
    booking_id: int,
    service: BookingServiceDep,
    user: CurrentUser,
) -> None:
    return await service.delete(booking_id, actor=user)
