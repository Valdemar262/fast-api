from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.repositories.booking import BookingRepository

BASE = datetime(2026, 9, 1, tzinfo=UTC)

CASES = [
    ("встык слева", 9, 10, False),
    ("внахлёст слева", 9.5, 10.5, True),
    ("точное совпадение", 10, 11, True),
    ("внутри", 10.25, 10.75, True),
    ("поглощает", 9, 12, True),
    ("внахлёст справа", 10.5, 11.5, True),
    ("встык справа", 11, 12, False),
]


def at(hour: float) -> datetime:
    return BASE + timedelta(hours=hour)


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [(c[1], c[2], c[3]) for c in CASES],
    ids=[c[0] for c in CASES],
)
async def test_has_overlap(
    session: AsyncSession,
    client_user: User,
    make_resource,
    make_booking,
    start: float,
    end: float,
    expected: bool,
) -> None:
    resource = await make_resource()
    await make_booking(client_user, resource, at(10), at(11))

    result = await BookingRepository(session).has_overlap(
        resource_id=resource.id, start_time=at(start), end_time=at(end)
    )

    assert result is expected
