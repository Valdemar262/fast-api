from abc import ABC

from app.models import Booking, Resource
from app.notification.base import BaseNotification


class BookingNotification(BaseNotification, ABC):
    def __init__(self, booking: Booking, resource: Resource) -> None:
        self.booking = booking
        self.resource = resource

    def _details(self) -> str:
        return (
            f"ID: {self.booking.id}\n"
            f"Resource: {self.resource.name}\n"
            f"From: {self.booking.start_time:%Y-%m-%d %H:%M}\n"
            f"To: {self.booking.end_time:%Y-%m-%d %H:%M}"
        )


class BookingCreatedNotification(BookingNotification):
    def subject(self) -> str:
        return "Booking created"

    def body(self) -> str:
        return f"Your booking has been created.\n\n{self._details()}"
