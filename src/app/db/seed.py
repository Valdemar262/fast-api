from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import AsyncSessionLocal
from app.enums import UserRole
from app.repositories.resource import ResourceRepository
from app.repositories.user import UserRepository

DEV_PASSWORD = "password123"

USERS = [
    ("Admin", "admin@example.com", UserRole.ADMIN),
    ("Client", "client@example.com", UserRole.CLIENT),
]

RESOURCES = [
    ("One-room apartment", "Room", "Room description"),
    ("Private house", "House", "House description"),
    ("Private villa", "Villa", "Villa description"),
]


async def truncate_all(session: AsyncSession) -> None:
    settings = get_settings()
    if settings.environment not in {"local", "test"}:
        raise RuntimeError(f"Refusing to truncate in environment={settings.environment!r}")

    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    await session.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))


async def seed(*, fresh: bool = False) -> None:
    async with AsyncSessionLocal() as session:

        if fresh:
            await truncate_all(session)

        user_repository = UserRepository(session)
        resource_repository = ResourceRepository(session)

        created_users = 0
        for name, email, role in USERS:
            if await user_repository.get_by_email(email) is not None:
                continue
            await user_repository.create(
                name=name,
                email=email,
                role=role,
                password_hash=hash_password(DEV_PASSWORD),
            )
            created_users += 1

        created_resources = 0
        if await resource_repository.count() == 0:
            for name, type_, description in RESOURCES:
                await resource_repository.create(
                    name=name,
                    type=type_,
                    description=description,
                )
                created_resources += 1

        await session.commit()

    print(f"Seeded: {created_users} users, {created_resources} resources")
    print(f"Dev password for all seeded users: {DEV_PASSWORD}")
