"""Integration tests: the right notification job is enqueued, after the commit.

These stop at the queue boundary — the spy replaces `.delay`, so nothing is
executed. What the job does once it runs is covered by
`tests/unit/test_mail_task.py`.
"""

import json
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.enums import StatementStatus
from app.models import User
from tests.conftest import MakeResource, MakeStatement

BASE = datetime(2026, 11, 1, tzinfo=UTC)


@pytest.fixture
def enqueued_tasks(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, str]]:
    """Record what was handed to Celery, patched where it is used."""
    enqueued: list[dict[str, str]] = []

    def fake_delay(**kwargs: str) -> None:
        enqueued.append(kwargs)

    monkeypatch.setattr("app.notification.base.send_email_task.delay", fake_delay)
    return enqueued


async def test_submit_enqueues_a_job_for_the_owner(
    client: AsyncClient,
    client_user: User,
    client_auth: dict[str, str],
    make_statement: MakeStatement,
    enqueued_tasks: list[dict[str, str]],
) -> None:
    statement = await make_statement(client_user, status=StatementStatus.DRAFT)

    await client.post(f"/api/v1/statements/{statement.id}/submit", headers=client_auth)

    assert len(enqueued_tasks) == 1
    assert enqueued_tasks[0]["to"] == client_user.email
    assert enqueued_tasks[0]["subject"] == "Statement submitted"


async def test_approve_enqueues_a_job_for_the_owner_not_the_admin(
    client: AsyncClient,
    client_user: User,
    admin_user: User,
    admin_auth: dict[str, str],
    make_statement: MakeStatement,
    make_resource: MakeResource,
    enqueued_tasks: list[dict[str, str]],
) -> None:
    """The mail goes to the statement's author, not to whoever pressed approve."""
    resource = await make_resource()
    statement = await make_statement(
        client_user, status=StatementStatus.SUBMITTED, resource_id=resource.id
    )

    await client.post(f"/api/v1/statements/{statement.id}/approve", headers=admin_auth)

    assert len(enqueued_tasks) == 1
    task = enqueued_tasks[0]
    assert task["to"] == client_user.email
    assert task["subject"] == "Statement approved"
    assert str(statement.number) in task["body"]


async def test_reject_enqueues_a_job_for_the_owner(
    client: AsyncClient,
    client_user: User,
    admin_auth: dict[str, str],
    make_statement: MakeStatement,
    enqueued_tasks: list[dict[str, str]],
) -> None:
    statement = await make_statement(client_user, status=StatementStatus.SUBMITTED)

    await client.post(f"/api/v1/statements/{statement.id}/reject", headers=admin_auth)

    assert len(enqueued_tasks) == 1
    assert enqueued_tasks[0]["subject"] == "Statement rejected"


async def test_a_refused_transition_enqueues_nothing(
    client: AsyncClient,
    client_user: User,
    admin_auth: dict[str, str],
    make_statement: MakeStatement,
    enqueued_tasks: list[dict[str, str]],
) -> None:
    """No state change means no job."""
    statement = await make_statement(client_user, status=StatementStatus.DRAFT)

    response = await client.post(f"/api/v1/statements/{statement.id}/approve", headers=admin_auth)

    assert response.status_code == 409
    assert enqueued_tasks == []


async def test_creating_a_booking_enqueues_a_job(
    client: AsyncClient,
    client_user: User,
    client_auth: dict[str, str],
    make_resource: MakeResource,
    enqueued_tasks: list[dict[str, str]],
) -> None:
    resource = await make_resource()

    await client.post(
        "/api/v1/bookings",
        json={
            "resource_id": resource.id,
            "start_time": BASE.isoformat(),
            "end_time": (BASE + timedelta(hours=1)).isoformat(),
        },
        headers=client_auth,
    )

    assert len(enqueued_tasks) == 1
    assert enqueued_tasks[0]["to"] == client_user.email
    assert enqueued_tasks[0]["subject"] == "Booking created"
    assert resource.name in enqueued_tasks[0]["body"]


async def test_a_conflicting_booking_enqueues_nothing(
    client: AsyncClient,
    client_user: User,
    client_auth: dict[str, str],
    make_resource: MakeResource,
    enqueued_tasks: list[dict[str, str]],
) -> None:
    resource = await make_resource()
    payload = {
        "resource_id": resource.id,
        "start_time": BASE.isoformat(),
        "end_time": (BASE + timedelta(hours=1)).isoformat(),
    }
    await client.post("/api/v1/bookings", json=payload, headers=client_auth)
    enqueued_tasks.clear()

    response = await client.post("/api/v1/bookings", json=payload, headers=client_auth)

    assert response.status_code == 409
    assert enqueued_tasks == []


async def test_enqueued_arguments_are_json_serialisable(
    client: AsyncClient,
    client_user: User,
    client_auth: dict[str, str],
    make_statement: MakeStatement,
    enqueued_tasks: list[dict[str, str]],
) -> None:
    """Celery serialises arguments as JSON — an ORM object would break the job."""
    statement = await make_statement(client_user, status=StatementStatus.DRAFT)

    await client.post(f"/api/v1/statements/{statement.id}/submit", headers=client_auth)

    json.dumps(enqueued_tasks[0])  # raises TypeError if a non-primitive slipped in
