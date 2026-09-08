from collections.abc import AsyncGenerator, Awaitable, Callable
from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.enums import StatementStatus, UserRole
from app.main import create_app
from app.models import Booking, Resource, Statement, User

settings = get_settings()

MakeStatement = Callable[..., Awaitable[Statement]]
MakeResource = Callable[..., Awaitable[Resource]]
MakeBooking = Callable[..., Awaitable[Booking]]


@pytest.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(settings.test_database_url, poolclass=NullPool)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    connection = await engine.connect()
    transaction = await connection.begin()

    session_factory = async_sessionmaker(
        bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )

    async with session_factory() as session:
        yield session

    await transaction.rollback()
    await connection.close()


@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()
    app.dependency_overrides[get_db] = lambda: session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def client_user(session: AsyncSession) -> User:
    user = User(
        name="Client",
        email="client@example.com",
        password_hash=hash_password("password123"),
        role=UserRole.CLIENT,
    )
    session.add(user)
    await session.flush()
    return user


@pytest.fixture
def client_auth(client_user: User) -> dict[str, str]:
    token = create_access_token(client_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_user(session: AsyncSession) -> User:
    user = User(
        name="Admin",
        email="admin@example.com",
        password_hash=hash_password("password123"),
        role=UserRole.ADMIN,
    )
    session.add(user)
    await session.flush()
    return user


@pytest.fixture
def admin_auth(admin_user: User) -> dict[str, str]:
    token = create_access_token(admin_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def make_statement(session: AsyncSession) -> MakeStatement:
    async def _make(
        user: User,
        *,
        status: StatementStatus = StatementStatus.DRAFT,
        resource_id: int | None = None,
    ) -> Statement:
        statement = Statement(
            title="Test statement",
            number=1,
            user_id=user.id,
            status=status,
            resource_id=resource_id,
        )

        session.add(statement)
        await session.flush()
        return statement

    return _make


@pytest.fixture
def make_resource(session: AsyncSession) -> MakeResource:
    async def _make(name: str = "Room A") -> Resource:
        resource = Resource(name=name, type="room")
        session.add(resource)
        await session.flush()
        return resource

    return _make


@pytest.fixture
def make_booking(session: AsyncSession) -> MakeBooking:
    async def _make(user: User, resource: Resource, start: datetime, end: datetime) -> Booking:
        booking = Booking(
            user_id=user.id,
            resource_id=resource.id,
            start_time=start,
            end_time=end,
        )
        session.add(booking)
        await session.flush()
        return booking

    return _make


@pytest.fixture(autouse=True)
def disable_mail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.mail.settings.mail_enabled", False)


@pytest.fixture(autouse=True)
def enqueued_tasks(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, str]]:
    enqueued: list[dict[str, str]] = []

    def fake_delay(**kwargs: str) -> None:
        enqueued.append(kwargs)

    monkeypatch.setattr("app.notification.base.send_email_task.delay", fake_delay)
    return enqueued
