from httpx import AsyncClient

from app.models import User

REGISTER_PAYLOAD = {
    "name": "New User",
    "email": "new@example.com",
    "password": "password123",
}


async def test_register_creates_client_and_returns_tokens(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "new@example.com"
    assert body["user"]["role"] == "client"
    assert body["tokens"]["token_type"] == "bearer"
    assert body["tokens"]["access_token"]
    assert body["tokens"]["refresh_token"]


async def test_register_never_returns_the_password_hash(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    assert "password_hash" not in response.json()["user"]
    assert "password" not in response.json()["user"]


async def test_register_rejects_duplicate_email(client: AsyncClient, client_user: User) -> None:
    payload = REGISTER_PAYLOAD | {"email": client_user.email}

    response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 409


async def test_register_rejects_short_password(client: AsyncClient) -> None:
    payload = REGISTER_PAYLOAD | {"password": "short"}

    response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 422


async def test_register_rejects_invalid_email(client: AsyncClient) -> None:
    payload = REGISTER_PAYLOAD | {"email": "not-an-email"}

    response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 422


async def test_register_ignores_role_from_the_request_body(client: AsyncClient) -> None:
    payload = REGISTER_PAYLOAD | {"role": "admin"}

    response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 201
    assert response.json()["user"]["role"] == "client"


async def test_login_returns_tokens(client: AsyncClient, client_user: User) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": client_user.email, "password": "password123"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["id"] == client_user.id


async def test_login_rejects_wrong_password(client: AsyncClient, client_user: User) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": client_user.email, "password": "wrong-password"},
    )

    assert response.status_code == 401


async def test_login_rejects_unknown_email(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


async def test_refresh_issues_a_new_token_pair(client: AsyncClient, client_user: User) -> None:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": client_user.email, "password": "password123"},
    )
    refresh_token = login.json()["tokens"]["refresh_token"]

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    assert response.json()["access_token"]


async def test_refresh_rejects_an_access_token(client: AsyncClient, client_user: User) -> None:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": client_user.email, "password": "password123"},
    )
    access_token = login.json()["tokens"]["access_token"]

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})

    assert response.status_code == 401


async def test_me_returns_the_authenticated_user(
    client: AsyncClient, client_user: User, client_auth: dict[str, str]
) -> None:
    response = await client.get("/api/v1/auth/me", headers=client_auth)

    assert response.status_code == 200
    assert response.json()["id"] == client_user.id


async def test_me_requires_a_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401


async def test_me_rejects_a_malformed_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer garbage"})

    assert response.status_code == 401
