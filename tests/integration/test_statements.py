from collections.abc import Awaitable, Callable

from httpx import AsyncClient

from app.enums import StatementStatus
from app.models import Resource, Statement, User

MakeStatement = Callable[..., Awaitable[Statement]]
MakeResource = Callable[..., Awaitable[Resource]]

CREATE_PAYLOAD = {"title": "Booking request", "number": 1}


async def test_create_requires_authentication(client: AsyncClient) -> None:
    response = await client.post("/api/v1/statements", json=CREATE_PAYLOAD)

    assert response.status_code == 401


async def test_create_always_starts_as_a_draft(
    client: AsyncClient, client_user: User, client_auth: dict[str, str]
) -> None:
    payload = CREATE_PAYLOAD | {"status": "approved"}

    response = await client.post("/api/v1/statements", json=payload, headers=client_auth)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "draft"
    assert body["user_id"] == client_user.id
    assert body["approved_by_id"] is None


async def test_create_rejects_a_short_title(
    client: AsyncClient, client_auth: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/statements", json=CREATE_PAYLOAD | {"title": "abc"}, headers=client_auth
    )

    assert response.status_code == 422


async def test_create_returns_404_for_a_missing_resource(
    client: AsyncClient, client_auth: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/statements",
        json=CREATE_PAYLOAD | {"resource_id": 999},
        headers=client_auth,
    )

    assert response.status_code == 404


async def test_client_sees_only_their_own_statements(
    client: AsyncClient,
    client_user: User,
    admin_user: User,
    client_auth: dict[str, str],
    make_statement: MakeStatement,
) -> None:
    await make_statement(client_user)
    await make_statement(client_user)
    await make_statement(admin_user)

    response = await client.get("/api/v1/statements", headers=client_auth)

    body = response.json()
    assert len(body["items"]) == 2
    assert body["total"] == 2
    assert all(item["user_id"] == client_user.id for item in body["items"])


async def test_admin_sees_every_statement(
    client: AsyncClient,
    client_user: User,
    admin_user: User,
    admin_auth: dict[str, str],
    make_statement: MakeStatement,
) -> None:
    await make_statement(client_user)
    await make_statement(client_user)
    await make_statement(admin_user)

    response = await client.get("/api/v1/statements", headers=admin_auth)

    body = response.json()
    assert len(body["items"]) == 3
    assert body["total"] == 3


async def test_owner_can_read_their_statement(
    client: AsyncClient,
    client_user: User,
    client_auth: dict[str, str],
    make_statement: MakeStatement,
) -> None:
    statement = await make_statement(client_user)

    response = await client.get(f"/api/v1/statements/{statement.id}", headers=client_auth)

    assert response.status_code == 200
    assert response.json()["id"] == statement.id


async def test_another_client_cannot_read_someone_elses_statement(
    client: AsyncClient,
    admin_user: User,
    client_auth: dict[str, str],
    make_statement: MakeStatement,
) -> None:
    statement = await make_statement(admin_user)

    response = await client.get(f"/api/v1/statements/{statement.id}", headers=client_auth)

    assert response.status_code == 403


async def test_admin_can_read_any_statement(
    client: AsyncClient,
    client_user: User,
    admin_auth: dict[str, str],
    make_statement: MakeStatement,
) -> None:
    statement = await make_statement(client_user)

    response = await client.get(f"/api/v1/statements/{statement.id}", headers=admin_auth)

    assert response.status_code == 200


async def test_read_requires_authentication(
    client: AsyncClient, client_user: User, make_statement: MakeStatement
) -> None:
    statement = await make_statement(client_user)

    response = await client.get(f"/api/v1/statements/{statement.id}")

    assert response.status_code == 401


async def test_update_requires_authentication(
    client: AsyncClient, client_user: User, make_statement: MakeStatement
) -> None:
    statement = await make_statement(client_user)

    response = await client.put(
        f"/api/v1/statements/{statement.id}", json={"title": "Anonymous edit"}
    )

    assert response.status_code == 401


async def test_update_by_another_client_is_forbidden(
    client: AsyncClient,
    admin_user: User,
    client_auth: dict[str, str],
    make_statement: MakeStatement,
) -> None:
    statement = await make_statement(admin_user)

    response = await client.put(
        f"/api/v1/statements/{statement.id}",
        json={"title": "Hijacked title"},
        headers=client_auth,
    )

    assert response.status_code == 403


async def test_delete_requires_authentication(
    client: AsyncClient, client_user: User, make_statement: MakeStatement
) -> None:
    statement = await make_statement(client_user)

    response = await client.delete(f"/api/v1/statements/{statement.id}")

    assert response.status_code == 401


async def test_deleted_statement_disappears_from_reads(
    client: AsyncClient,
    client_user: User,
    client_auth: dict[str, str],
    make_statement: MakeStatement,
) -> None:
    statement = await make_statement(client_user)

    delete = await client.delete(f"/api/v1/statements/{statement.id}", headers=client_auth)
    assert delete.status_code == 204

    follow_up = await client.get(f"/api/v1/statements/{statement.id}", headers=client_auth)
    assert follow_up.status_code == 404

    listing = await client.get("/api/v1/statements", headers=client_auth)
    assert listing.json()["total"] == 0


async def test_submit_moves_a_draft_to_submitted(
    client: AsyncClient,
    client_user: User,
    client_auth: dict[str, str],
    make_statement: MakeStatement,
) -> None:
    statement = await make_statement(client_user, status=StatementStatus.DRAFT)

    response = await client.post(f"/api/v1/statements/{statement.id}/submit", headers=client_auth)

    assert response.status_code == 200
    assert response.json()["status"] == "submitted"


async def test_submitting_twice_is_a_conflict(
    client: AsyncClient,
    client_user: User,
    client_auth: dict[str, str],
    make_statement: MakeStatement,
) -> None:
    statement = await make_statement(client_user, status=StatementStatus.SUBMITTED)

    response = await client.post(f"/api/v1/statements/{statement.id}/submit", headers=client_auth)

    assert response.status_code == 409


async def test_approve_is_forbidden_for_a_client(
    client: AsyncClient,
    client_user: User,
    client_auth: dict[str, str],
    make_statement: MakeStatement,
) -> None:
    statement = await make_statement(client_user, status=StatementStatus.SUBMITTED)

    response = await client.post(f"/api/v1/statements/{statement.id}/approve", headers=client_auth)

    assert response.status_code == 403


async def test_approve_by_an_admin_records_the_approver(
    client: AsyncClient,
    client_user: User,
    admin_user: User,
    admin_auth: dict[str, str],
    make_statement: MakeStatement,
    make_resource: MakeResource,
) -> None:
    resource = await make_resource()
    statement = await make_statement(
        client_user, status=StatementStatus.SUBMITTED, resource_id=resource.id
    )

    response = await client.post(f"/api/v1/statements/{statement.id}/approve", headers=admin_auth)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert body["approved_by_id"] == admin_user.id


async def test_approving_a_draft_is_a_conflict(
    client: AsyncClient,
    client_user: User,
    admin_auth: dict[str, str],
    make_statement: MakeStatement,
) -> None:
    statement = await make_statement(client_user, status=StatementStatus.DRAFT)

    response = await client.post(f"/api/v1/statements/{statement.id}/approve", headers=admin_auth)

    assert response.status_code == 409


async def test_rejecting_an_approved_statement_is_a_conflict(
    client: AsyncClient,
    client_user: User,
    admin_auth: dict[str, str],
    make_statement: MakeStatement,
) -> None:
    statement = await make_statement(client_user, status=StatementStatus.APPROVED)

    response = await client.post(f"/api/v1/statements/{statement.id}/reject", headers=admin_auth)

    assert response.status_code == 409


async def test_transition_on_a_missing_statement_is_404(
    client: AsyncClient, client_auth: dict[str, str]
) -> None:
    response = await client.post("/api/v1/statements/999/submit", headers=client_auth)

    assert response.status_code == 404
