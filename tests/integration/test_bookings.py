from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.models import User
from tests.conftest import MakeBooking, MakeResource

BASE = datetime(2026, 10, 1, tzinfo=UTC)


def at(hour: float) -> str:
    return (BASE + timedelta(hours=hour)).isoformat()


async def test_create_requires_authentication(
    client: AsyncClient, make_resource: MakeResource
) -> None:
    resource = await make_resource()

    response = await client.post(
        "/api/v1/bookings",
        json={"resource_id": resource.id, "start_time": at(10), "end_time": at(11)},
    )

    assert response.status_code == 401


async def test_create_succeeds_and_takes_the_owner_from_the_token(
    client: AsyncClient,
    client_user: User,
    client_auth: dict[str, str],
    make_resource: MakeResource,
) -> None:
    resource = await make_resource()

    response = await client.post(
        "/api/v1/bookings",
        json={
            "resource_id": resource.id,
            "start_time": at(10),
            "end_time": at(11),
            "user_id": 999,
        },
        headers=client_auth,
    )

    assert response.status_code == 201
    assert response.json()["user_id"] == client_user.id


async def test_create_returns_404_for_a_missing_resource(
    client: AsyncClient, client_auth: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/bookings",
        json={"resource_id": 999, "start_time": at(10), "end_time": at(11)},
        headers=client_auth,
    )

    assert response.status_code == 404


async def test_create_rejects_an_inverted_time_range(
    client: AsyncClient, client_auth: dict[str, str], make_resource: MakeResource
) -> None:
    resource = await make_resource()

    response = await client.post(
        "/api/v1/bookings",
        json={"resource_id": resource.id, "start_time": at(12), "end_time": at(10)},
        headers=client_auth,
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("start", "end", "expected_status"),
    [
        (9, 10, 201),
        (9.5, 10.5, 409),
        (10, 11, 409),
        (10.25, 10.75, 409),
        (9, 12, 409),
        (10.5, 11.5, 409),
        (11, 12, 201),
    ],
    ids=[
        "touching_left",
        "overlap_left",
        "exact_match",
        "contained",
        "contains",
        "overlap_right",
        "touching_right",
    ],
)
async def test_conflict_detection(
    client: AsyncClient,
    client_user: User,
    client_auth: dict[str, str],
    make_resource: MakeResource,
    make_booking: MakeBooking,
    start: float,
    end: float,
    expected_status: int,
) -> None:
    resource = await make_resource()
    await make_booking(
        client_user, resource, BASE + timedelta(hours=10), BASE + timedelta(hours=11)
    )

    response = await client.post(
        "/api/v1/bookings",
        json={"resource_id": resource.id, "start_time": at(start), "end_time": at(end)},
        headers=client_auth,
    )

    assert response.status_code == expected_status


async def test_the_same_slot_on_another_resource_is_allowed(
    client: AsyncClient,
    client_user: User,
    client_auth: dict[str, str],
    make_resource: MakeResource,
    make_booking: MakeBooking,
) -> None:
    first = await make_resource(name="Room 1")
    second = await make_resource(name="Room 2")
    await make_booking(client_user, first, BASE + timedelta(hours=10), BASE + timedelta(hours=11))

    response = await client.post(
        "/api/v1/bookings",
        json={"resource_id": second.id, "start_time": at(10), "end_time": at(11)},
        headers=client_auth,
    )

    assert response.status_code == 201


async def test_list_for_resource_is_ordered_by_start_time(
    client: AsyncClient,
    client_user: User,
    client_auth: dict[str, str],
    make_resource: MakeResource,
    make_booking: MakeBooking,
) -> None:
    resource = await make_resource()
    for hour in (14, 10, 12):
        await make_booking(
            client_user,
            resource,
            BASE + timedelta(hours=hour),
            BASE + timedelta(hours=hour + 1),
        )

    response = await client.get(f"/api/v1/resources/{resource.id}/bookings", headers=client_auth)

    starts = [item["start_time"] for item in response.json()["items"]]
    assert starts == sorted(starts)


async def test_list_for_a_missing_resource_is_404(
    client: AsyncClient, client_auth: dict[str, str]
) -> None:
    response = await client.get("/api/v1/resources/999/bookings", headers=client_auth)

    assert response.status_code == 404


async def test_delete_own_booking(
    client: AsyncClient,
    client_user: User,
    client_auth: dict[str, str],
    make_resource: MakeResource,
    make_booking: MakeBooking,
) -> None:
    resource = await make_resource()
    booking = await make_booking(
        client_user, resource, BASE + timedelta(hours=10), BASE + timedelta(hours=11)
    )

    response = await client.delete(f"/api/v1/bookings/{booking.id}", headers=client_auth)

    assert response.status_code == 204


async def test_delete_someone_elses_booking_is_forbidden(
    client: AsyncClient,
    admin_user: User,
    client_auth: dict[str, str],
    make_resource: MakeResource,
    make_booking: MakeBooking,
) -> None:
    resource = await make_resource()
    booking = await make_booking(
        admin_user, resource, BASE + timedelta(hours=10), BASE + timedelta(hours=11)
    )

    response = await client.delete(f"/api/v1/bookings/{booking.id}", headers=client_auth)

    assert response.status_code == 403


async def test_admin_may_delete_any_booking(
    client: AsyncClient,
    client_user: User,
    admin_auth: dict[str, str],
    make_resource: MakeResource,
    make_booking: MakeBooking,
) -> None:
    resource = await make_resource()
    booking = await make_booking(
        client_user, resource, BASE + timedelta(hours=10), BASE + timedelta(hours=11)
    )

    response = await client.delete(f"/api/v1/bookings/{booking.id}", headers=admin_auth)

    assert response.status_code == 204


async def test_delete_a_missing_booking_is_404(
    client: AsyncClient, admin_auth: dict[str, str]
) -> None:
    response = await client.delete("/api/v1/bookings/999", headers=admin_auth)

    assert response.status_code == 404
