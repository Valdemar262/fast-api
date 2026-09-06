from sqlalchemy import func, select

from app.enums import UserRole
from app.models import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        user: User | None = await self.session.scalar(stmt)
        return user

    async def get_all(self, *, limit: int, offset: int) -> list[User]:
        stmt = select(User).offset(offset).limit(limit)
        results = await self.session.scalars(stmt)
        return list(results)

    async def count_by_role(self, role: UserRole) -> int:
        stmt = select(func.count()).select_from(User).where(User.role == role)
        return await self.session.scalar(stmt) or 0
