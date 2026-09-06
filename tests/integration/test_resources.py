from collections.abc import Awaitable, Callable

from httpx import AsyncClient

from app.models import Resource

MakeResource = Callable[..., Awaitable[Resource]]

CREATE_PAYLOAD = {"name": "Room B", "type": "room", "description": "Six seats"}


async def test_list_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/resources")

    assert response.status_code == 401


async def test_list_returns_an_empty_page_when_there_is_nothing(
    client: AsyncClient, client_auth: dict[str, str]
) -> None:
    response = await client.get("/api/v1/resources", headers=client_auth)

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": 50, "offset": 0}


async def test_list_items_and_total_agree(
    client: AsyncClient, client_auth: dict[str, str], make_resource: MakeResource
) -> None:
    for index in range(3):
        await make_resource(name=f"Room {index}")

    response = await client.get("/api/v1/resources", headers=client_auth)

    body = response.json()
    assert len(body["items"]) == 3
    assert body["total"] == 3


async def test_list_respects_limit_and_offset(
    client: AsyncClient, client_auth: dict[str, str], make_resource: MakeResource
) -> None:
    for index in range(3):
        await make_resource(name=f"Room {index}")

    response = await client.get(
        "/api/v1/resources", params={"limit": 2, "offset": 1}, headers=client_auth
    )

    body = response.json()
    assert len(body["items"]) == 2
    assert body["total"] == 3


async def test_list_rejects_limit_above_the_maximum(
    client: AsyncClient, client_auth: dict[str, str]
) -> None:
    response = await client.get("/api/v1/resources", params={"limit": 999}, headers=client_auth)

    assert response.status_code == 422


async def test_get_returns_404_for_a_missing_resource(
    client: AsyncClient, client_auth: dict[str, str]
) -> None:
    response = await client.get("/api/v1/resources/999", headers=client_auth)

    assert response.status_code == 404


async def test_get_rejects_a_non_numeric_id(
    client: AsyncClient, client_auth: dict[str, str]
) -> None:
    response = await client.get("/api/v1/resources/abc", headers=client_auth)

    assert response.status_code == 422


async def test_create_is_forbidden_for_a_client(
    client: AsyncClient, client_auth: dict[str, str]
) -> None:
    response = await client.post("/api/v1/resources", json=CREATE_PAYLOAD, headers=client_auth)

    assert response.status_code == 403


async def test_create_succeeds_for_an_admin(
    client: AsyncClient, admin_auth: dict[str, str]
) -> None:
    response = await client.post("/api/v1/resources", json=CREATE_PAYLOAD, headers=admin_auth)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Room B"
    assert body["id"]


async def test_create_rejects_an_empty_name(
    client: AsyncClient, admin_auth: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/resources", json=CREATE_PAYLOAD | {"name": ""}, headers=admin_auth
    )

    assert response.status_code == 422


async def test_update_changes_only_the_fields_that_were_sent(
    client: AsyncClient, admin_auth: dict[str, str], make_resource: MakeResource
) -> None:
    resource = await make_resource(name="Original")

    response = await client.put(
        f"/api/v1/resources/{resource.id}",
        json={"description": "Updated description"},
        headers=admin_auth,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["description"] == "Updated description"
    assert body["name"] == "Original"
    assert body["type"] == "room"


async def test_update_is_forbidden_for_a_client(
    client: AsyncClient, client_auth: dict[str, str], make_resource: MakeResource
) -> None:
    resource = await make_resource()

    response = await client.put(
        f"/api/v1/resources/{resource.id}", json={"name": "Hacked"}, headers=client_auth
    )

    assert response.status_code == 403


async def test_delete_removes_the_resource(
    client: AsyncClient, admin_auth: dict[str, str], make_resource: MakeResource
) -> None:
    resource = await make_resource()

    response = await client.delete(f"/api/v1/resources/{resource.id}", headers=admin_auth)
    assert response.status_code == 204

    follow_up = await client.get(f"/api/v1/resources/{resource.id}", headers=admin_auth)
    assert follow_up.status_code == 404


async def test_delete_is_forbidden_for_a_client(
    client: AsyncClient, client_auth: dict[str, str], make_resource: MakeResource
) -> None:
    resource = await make_resource()

    response = await client.delete(f"/api/v1/resources/{resource.id}", headers=client_auth)

    assert response.status_code == 403
