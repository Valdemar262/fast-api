import csv
import io
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import StatementStatus
from app.models import User
from tests.conftest import MakeBooking, MakeResource, MakeStatement

BASE = datetime(2026, 12, 1, tzinfo=UTC)


def parse_csv(body: str) -> list[list[str]]:
    return list(csv.reader(io.StringIO(body)))


async def test_reports_require_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/reports/user_activity")

    assert response.status_code == 401


async def test_reports_are_forbidden_for_a_client(
    client: AsyncClient, client_auth: dict[str, str]
) -> None:
    response = await client.get("/api/v1/reports/user_activity", headers=client_auth)

    assert response.status_code == 403


@pytest.mark.parametrize(
    "report_type",
    ["statements_summary", "bookings_by_resource", "user_activity", "statements_trend"],
)
async def test_every_report_is_served_as_a_csv_attachment(
    client: AsyncClient, admin_auth: dict[str, str], report_type: str
) -> None:
    response = await client.get(f"/api/v1/reports/{report_type}", headers=admin_auth)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert report_type in response.headers["content-disposition"]
    assert response.headers["content-disposition"].startswith("attachment;")


async def test_an_unknown_report_type_is_rejected(
    client: AsyncClient, admin_auth: dict[str, str]
) -> None:
    response = await client.get("/api/v1/reports/does_not_exist", headers=admin_auth)

    assert response.status_code == 422


async def test_an_unknown_period_is_rejected(
    client: AsyncClient, admin_auth: dict[str, str]
) -> None:
    response = await client.get(
        "/api/v1/reports/user_activity", params={"period": "century"}, headers=admin_auth
    )

    assert response.status_code == 422


async def test_statements_summary_lists_every_status_including_empty_ones(
    client: AsyncClient,
    client_user: User,
    admin_auth: dict[str, str],
    make_statement: MakeStatement,
) -> None:
    await make_statement(client_user, status=StatementStatus.DRAFT)
    await make_statement(client_user, status=StatementStatus.DRAFT)
    await make_statement(client_user, status=StatementStatus.APPROVED)

    response = await client.get(
        "/api/v1/reports/statements_summary", params={"period": "all"}, headers=admin_auth
    )

    rows = dict(row for row in parse_csv(response.text)[1:])
    assert rows == {
        "draft": "2",
        "submitted": "0",
        "approved": "1",
        "rejected": "0",
        "total": "3",
    }


async def test_statements_summary_respects_the_period(
    client: AsyncClient,
    client_user: User,
    admin_auth: dict[str, str],
    make_statement: MakeStatement,
    session: AsyncSession,
) -> None:
    recent = await make_statement(client_user, status=StatementStatus.DRAFT)
    old = await make_statement(client_user, status=StatementStatus.DRAFT)
    old.created_at = datetime.now(UTC) - timedelta(days=400)
    await session.flush()

    response = await client.get(
        "/api/v1/reports/statements_summary", params={"period": "month"}, headers=admin_auth
    )

    rows = dict(row for row in parse_csv(response.text)[1:])
    assert rows["draft"] == "1"
    assert rows["total"] == "1"
    assert recent.id != old.id


async def test_bookings_by_resource_keeps_resources_without_bookings(
    client: AsyncClient,
    client_user: User,
    admin_auth: dict[str, str],
    make_resource: MakeResource,
    make_booking: MakeBooking,
) -> None:
    booked = await make_resource(name="Booked room")
    await make_resource(name="Idle room")
    await make_booking(client_user, booked, BASE, BASE + timedelta(hours=1))

    response = await client.get("/api/v1/reports/bookings_by_resource", headers=admin_auth)

    rows = {row[1]: row[2] for row in parse_csv(response.text)[1:]}
    assert rows == {"Booked room": "1", "Idle room": "0"}


async def test_user_activity_counts_are_not_multiplied(
    client: AsyncClient,
    client_user: User,
    admin_user: User,
    admin_auth: dict[str, str],
    make_statement: MakeStatement,
    make_resource: MakeResource,
    make_booking: MakeBooking,
) -> None:
    resource = await make_resource()
    for _ in range(3):
        await make_statement(client_user)
    await make_booking(client_user, resource, BASE, BASE + timedelta(hours=1))
    await make_booking(client_user, resource, BASE + timedelta(hours=2), BASE + timedelta(hours=3))

    response = await client.get("/api/v1/reports/user_activity", headers=admin_auth)

    rows = {row[2]: (row[3], row[4]) for row in parse_csv(response.text)[1:]}
    assert rows[client_user.email] == ("3", "2")
    assert rows[admin_user.email] == ("0", "0")


async def test_user_activity_ignores_soft_deleted_statements(
    client: AsyncClient,
    client_user: User,
    admin_auth: dict[str, str],
    make_statement: MakeStatement,
    client_auth: dict[str, str],
) -> None:
    statement = await make_statement(client_user)
    await make_statement(client_user)
    await client.delete(f"/api/v1/statements/{statement.id}", headers=client_auth)

    response = await client.get("/api/v1/reports/user_activity", headers=admin_auth)

    rows = {row[2]: row[3] for row in parse_csv(response.text)[1:]}
    assert rows[client_user.email] == "1"


async def test_statements_trend_groups_by_day(
    client: AsyncClient,
    client_user: User,
    admin_auth: dict[str, str],
    make_statement: MakeStatement,
) -> None:
    for _ in range(3):
        await make_statement(client_user)

    response = await client.get(
        "/api/v1/reports/statements_trend", params={"period": "all"}, headers=admin_auth
    )

    data = parse_csv(response.text)
    assert data[0] == ["Day", "Count"]
    assert len(data) == 2  # a single day
    assert data[1][1] == "3"


async def test_an_empty_report_still_has_its_header(
    client: AsyncClient, admin_auth: dict[str, str]
) -> None:
    response = await client.get(
        "/api/v1/reports/statements_trend", params={"period": "all"}, headers=admin_auth
    )

    assert response.status_code == 200
    assert parse_csv(response.text) == [["Day", "Count"]]
