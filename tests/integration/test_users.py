from httpx import AsyncClient

from app.models import User


async def test_list_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users")

    assert response.status_code == 401


async def test_list_is_forbidden_for_a_client(
    client: AsyncClient, client_auth: dict[str, str]
) -> None:
    response = await client.get("/api/v1/users", headers=client_auth)

    assert response.status_code == 403


async def test_list_for_an_admin_agrees_on_items_and_total(
    client: AsyncClient, client_user: User, admin_user: User, admin_auth: dict[str, str]
) -> None:
    response = await client.get("/api/v1/users", headers=admin_auth)

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == body["total"] == 2


async def test_list_never_exposes_password_hashes(
    client: AsyncClient, client_user: User, admin_auth: dict[str, str]
) -> None:
    response = await client.get("/api/v1/users", headers=admin_auth)

    assert all("password_hash" not in item for item in response.json()["items"])


async def test_client_can_read_their_own_profile(
    client: AsyncClient, client_user: User, client_auth: dict[str, str]
) -> None:
    response = await client.get(f"/api/v1/users/{client_user.id}", headers=client_auth)

    assert response.status_code == 200
    assert response.json()["email"] == client_user.email


async def test_client_cannot_read_another_profile(
    client: AsyncClient, admin_user: User, client_auth: dict[str, str]
) -> None:
    response = await client.get(f"/api/v1/users/{admin_user.id}", headers=client_auth)

    assert response.status_code == 403


async def test_admin_can_read_any_profile(
    client: AsyncClient, client_user: User, admin_auth: dict[str, str]
) -> None:
    response = await client.get(f"/api/v1/users/{client_user.id}", headers=admin_auth)

    assert response.status_code == 200


async def test_update_me_changes_only_the_fields_that_were_sent(
    client: AsyncClient, client_user: User, client_auth: dict[str, str]
) -> None:
    original_name = client_user.name

    response = await client.patch(
        "/api/v1/users/me", json={"phone": "+70000000000"}, headers=client_auth
    )

    assert response.status_code == 200
    body = response.json()
    assert body["phone"] == "+70000000000"
    assert body["name"] == original_name


async def test_update_me_cannot_change_the_role(
    client: AsyncClient, client_user: User, client_auth: dict[str, str]
) -> None:
    response = await client.patch("/api/v1/users/me", json={"role": "admin"}, headers=client_auth)

    assert response.status_code == 200
    assert response.json()["role"] == "client"


async def test_update_me_requires_authentication(client: AsyncClient) -> None:
    response = await client.patch("/api/v1/users/me", json={"phone": "+70000000000"})

    assert response.status_code == 401


async def test_role_change_is_forbidden_for_a_client(
    client: AsyncClient, admin_user: User, client_auth: dict[str, str]
) -> None:
    response = await client.patch(
        f"/api/v1/users/{admin_user.id}/role",
        json={"role": "client"},
        headers=client_auth,
    )

    assert response.status_code == 403


async def test_admin_can_promote_a_client(
    client: AsyncClient, client_user: User, admin_auth: dict[str, str]
) -> None:
    response = await client.patch(
        f"/api/v1/users/{client_user.id}/role",
        json={"role": "admin"},
        headers=admin_auth,
    )

    assert response.status_code == 200
    assert response.json()["role"] == "admin"


async def test_the_last_admin_cannot_be_demoted(
    client: AsyncClient, admin_user: User, admin_auth: dict[str, str]
) -> None:
    response = await client.patch(
        f"/api/v1/users/{admin_user.id}/role",
        json={"role": "client"},
        headers=admin_auth,
    )

    assert response.status_code == 403


async def test_an_admin_can_be_demoted_while_another_one_remains(
    client: AsyncClient,
    admin_user: User,
    client_user: User,
    admin_auth: dict[str, str],
) -> None:
    await client.patch(
        f"/api/v1/users/{client_user.id}/role",
        json={"role": "admin"},
        headers=admin_auth,
    )

    response = await client.patch(
        f"/api/v1/users/{client_user.id}/role",
        json={"role": "client"},
        headers=admin_auth,
    )

    assert response.status_code == 200


async def test_role_change_rejects_an_unknown_role(
    client: AsyncClient, client_user: User, admin_auth: dict[str, str]
) -> None:
    response = await client.patch(
        f"/api/v1/users/{client_user.id}/role",
        json={"role": "superuser"},
        headers=admin_auth,
    )

    assert response.status_code == 422


async def test_admin_cannot_delete_themselves(
    client: AsyncClient, admin_user: User, admin_auth: dict[str, str]
) -> None:
    response = await client.delete(f"/api/v1/users/{admin_user.id}", headers=admin_auth)

    assert response.status_code == 403


async def test_admin_can_delete_another_user(
    client: AsyncClient, client_user: User, admin_auth: dict[str, str]
) -> None:
    response = await client.delete(f"/api/v1/users/{client_user.id}", headers=admin_auth)
    assert response.status_code == 204

    follow_up = await client.get(f"/api/v1/users/{client_user.id}", headers=admin_auth)
    assert follow_up.status_code == 404


async def test_delete_is_forbidden_for_a_client(
    client: AsyncClient, admin_user: User, client_auth: dict[str, str]
) -> None:
    response = await client.delete(f"/api/v1/users/{admin_user.id}", headers=client_auth)

    assert response.status_code == 403


async def test_delete_a_missing_user_is_404(
    client: AsyncClient, admin_auth: dict[str, str]
) -> None:
    response = await client.delete("/api/v1/users/999", headers=admin_auth)

    assert response.status_code == 404
