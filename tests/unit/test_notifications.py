from datetime import UTC, datetime

from app.models import Booking, Resource, Statement
from app.notification import (
    BookingCreatedNotification,
    StatementApprovedNotification,
    StatementRejectedNotification,
    StatementSubmittedNotification,
)


def _statement() -> Statement:
    return Statement(id=1, title="Room request", number=42, date=None)


def test_submitted_notification_content() -> None:
    notification = StatementSubmittedNotification(_statement())

    assert notification.subject() == "Statement submitted"
    assert "submitted for review" in notification.body()


def test_approved_notification_mentions_the_statement_details() -> None:
    notification = StatementApprovedNotification(_statement())

    assert notification.subject() == "Statement approved"
    body = notification.body()
    assert "approved" in body
    assert "42" in body
    assert "Room request" in body


def test_rejected_notification_content() -> None:
    notification = StatementRejectedNotification(_statement())

    assert notification.subject() == "Statement rejected"
    assert "rejected" in notification.body()


def test_booking_created_notification_mentions_the_resource_and_time() -> None:
    resource = Resource(id=1, name="Room A", type="room")
    booking = Booking(
        id=7,
        user_id=1,
        resource_id=1,
        start_time=datetime(2026, 10, 1, 10, 0, tzinfo=UTC),
        end_time=datetime(2026, 10, 1, 11, 0, tzinfo=UTC),
    )

    notification = BookingCreatedNotification(booking, resource)

    assert notification.subject() == "Booking created"
    body = notification.body()
    assert "Room A" in body
    assert "2026-10-01 10:00" in body
    assert "2026-10-01 11:00" in body
