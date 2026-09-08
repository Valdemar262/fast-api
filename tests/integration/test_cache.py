import pytest
from httpx import AsyncClient

from app.cache.keys import RESOURCE_LIST_PREFIX, resource_key, resource_list_key
from app.core.cache import redis_client
from app.models import Resource
from app.repositories.resource import ResourceRepository
from tests.conftest import MakeResource

CREATE_PAYLOAD = {"name": "Room B", "type": "room", "description": "Six seats"}


@pytest.fixture
def repository_calls(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    calls: list[int] = []
    original = ResourceRepository.get_by_id

    async def counting_get_by_id(self: ResourceRepository, entity_id: int) -> Resource | None:
        calls.append(entity_id)
        return await original(self, entity_id)

    monkeypatch.setattr(ResourceRepository, "get_by_id", counting_get_by_id)
    return calls


async def test_a_read_populates_the_cache(
    client: AsyncClient, client_auth: dict[str, str], make_resource: MakeResource
) -> None:
    resource = await make_resource()
    assert await redis_client.get(resource_key(resource.id)) is None

    response = await client.get(f"/api/v1/resources/{resource.id}", headers=client_auth)

    assert response.status_code == 200
    assert await redis_client.get(resource_key(resource.id)) is not None


async def test_the_cached_entry_expires(
    client: AsyncClient, client_auth: dict[str, str], make_resource: MakeResource
) -> None:
    resource = await make_resource()

    await client.get(f"/api/v1/resources/{resource.id}", headers=client_auth)

    ttl = await redis_client.ttl(resource_key(resource.id))
    assert 0 < ttl <= 300


async def test_a_second_read_does_not_hit_the_database(
    client: AsyncClient,
    client_auth: dict[str, str],
    make_resource: MakeResource,
    repository_calls: list[int],
) -> None:
    resource = await make_resource()

    await client.get(f"/api/v1/resources/{resource.id}", headers=client_auth)
    calls_after_first_read = len(repository_calls)

    await client.get(f"/api/v1/resources/{resource.id}", headers=client_auth)

    assert calls_after_first_read == 1
    assert len(repository_calls) == 1


async def test_both_reads_return_the_same_payload(
    client: AsyncClient, client_auth: dict[str, str], make_resource: MakeResource
) -> None:
    resource = await make_resource()

    first = await client.get(f"/api/v1/resources/{resource.id}", headers=client_auth)
    second = await client.get(f"/api/v1/resources/{resource.id}", headers=client_auth)

    assert first.json() == second.json()


async def test_a_list_read_populates_its_own_key(
    client: AsyncClient, client_auth: dict[str, str], make_resource: MakeResource
) -> None:
    await make_resource()

    await client.get("/api/v1/resources", params={"limit": 10, "offset": 0}, headers=client_auth)

    assert await redis_client.get(resource_list_key(limit=10, offset=0)) is not None


async def test_pages_are_cached_separately(
    client: AsyncClient, client_auth: dict[str, str], make_resource: MakeResource
) -> None:
    for index in range(3):
        await make_resource(name=f"Room {index}")

    await client.get("/api/v1/resources", params={"limit": 2, "offset": 0}, headers=client_auth)
    await client.get("/api/v1/resources", params={"limit": 2, "offset": 2}, headers=client_auth)

    assert await redis_client.get(resource_list_key(limit=2, offset=0)) is not None
    assert await redis_client.get(resource_list_key(limit=2, offset=2)) is not None


async def test_update_invalidates_the_entry(
    client: AsyncClient,
    client_auth: dict[str, str],
    admin_auth: dict[str, str],
    make_resource: MakeResource,
) -> None:
    resource = await make_resource(name="Original")
    await client.get(f"/api/v1/resources/{resource.id}", headers=client_auth)

    await client.put(
        f"/api/v1/resources/{resource.id}",
        json={"description": "Updated"},
        headers=admin_auth,
    )

    assert await redis_client.get(resource_key(resource.id)) is None


async def test_a_read_after_update_returns_fresh_data(
    client: AsyncClient,
    client_auth: dict[str, str],
    admin_auth: dict[str, str],
    make_resource: MakeResource,
) -> None:
    resource = await make_resource(name="Original")
    await client.get(f"/api/v1/resources/{resource.id}", headers=client_auth)

    await client.put(
        f"/api/v1/resources/{resource.id}",
        json={"description": "Updated"},
        headers=admin_auth,
    )
    response = await client.get(f"/api/v1/resources/{resource.id}", headers=client_auth)

    assert response.json()["description"] == "Updated"


async def test_delete_invalidates_the_entry(
    client: AsyncClient,
    client_auth: dict[str, str],
    admin_auth: dict[str, str],
    make_resource: MakeResource,
) -> None:
    resource = await make_resource()
    await client.get(f"/api/v1/resources/{resource.id}", headers=client_auth)

    await client.delete(f"/api/v1/resources/{resource.id}", headers=admin_auth)

    assert await redis_client.get(resource_key(resource.id)) is None

    follow_up = await client.get(f"/api/v1/resources/{resource.id}", headers=client_auth)
    assert follow_up.status_code == 404


async def test_create_invalidates_the_list_pages(
    client: AsyncClient,
    client_auth: dict[str, str],
    admin_auth: dict[str, str],
    make_resource: MakeResource,
) -> None:
    await make_resource()
    await client.get("/api/v1/resources", params={"limit": 10, "offset": 0}, headers=client_auth)

    await client.post("/api/v1/resources", json=CREATE_PAYLOAD, headers=admin_auth)

    assert await redis_client.get(resource_list_key(limit=10, offset=0)) is None


async def test_a_list_read_after_create_shows_the_new_resource(
    client: AsyncClient,
    client_auth: dict[str, str],
    admin_auth: dict[str, str],
    make_resource: MakeResource,
) -> None:
    await make_resource()
    first = await client.get(
        "/api/v1/resources", params={"limit": 10, "offset": 0}, headers=client_auth
    )
    assert first.json()["total"] == 1

    await client.post("/api/v1/resources", json=CREATE_PAYLOAD, headers=admin_auth)
    second = await client.get(
        "/api/v1/resources", params={"limit": 10, "offset": 0}, headers=client_auth
    )

    assert second.json()["total"] == 2


async def test_update_invalidates_every_list_page(
    client: AsyncClient,
    client_auth: dict[str, str],
    admin_auth: dict[str, str],
    make_resource: MakeResource,
) -> None:
    resources = [await make_resource(name=f"Room {index}") for index in range(3)]
    await client.get("/api/v1/resources", params={"limit": 2, "offset": 0}, headers=client_auth)
    await client.get("/api/v1/resources", params={"limit": 2, "offset": 2}, headers=client_auth)

    await client.put(
        f"/api/v1/resources/{resources[0].id}",
        json={"description": "Updated"},
        headers=admin_auth,
    )

    remaining = [key async for key in redis_client.scan_iter(match=f"{RESOURCE_LIST_PREFIX}*")]
    assert remaining == []


async def test_the_api_still_works_when_redis_is_down(
    client: AsyncClient,
    client_auth: dict[str, str],
    make_resource: MakeResource,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resource = await make_resource()

    async def broken(*args: object, **kwargs: object) -> None:
        raise ConnectionError("Redis is unavailable")

    monkeypatch.setattr("app.core.cache.redis_client.get", broken)
    monkeypatch.setattr("app.core.cache.redis_client.set", broken)

    response = await client.get(f"/api/v1/resources/{resource.id}", headers=client_auth)

    assert response.status_code == 200
    assert response.json()["id"] == resource.id
