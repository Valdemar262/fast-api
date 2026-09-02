from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import UserRole
from app.exceptions import NotFoundError, PermissionDeniedError
from app.models import User
from app.repositories.user import UserRepository
from app.schemas import Page, RoleUpdate, UserRead, UserUpdate


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)

    async def get(self, user_id: int) -> User:
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user

    async def list_users(self, *, limit: int, offset: int) -> Page[UserRead]:
        items = await self.users.get_all(limit=limit, offset=offset)
        total = await self.users.count()
        return Page(
            items=[UserRead.model_validate(item) for item in items],
            total=total,
            offset=offset,
            limit=limit,
        )

    async def get_profile(self, user_id: int, actor: User) -> UserRead:
        user = await self.get(user_id)

        if user.id != actor.id and actor.role != UserRole.ADMIN:
            raise PermissionDeniedError("You can only view your own profile")

        return UserRead.model_validate(user)

    async def update(self, actor: User, payload: UserUpdate) -> User:
        user = await self.get(actor.id)

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(user, field, value)

        await self.session.commit()
        return user

    async def update_role(self, user_id: int, payload: RoleUpdate) -> User:
        user = await self.get(user_id)

        if user.role == UserRole.ADMIN and payload.role != UserRole.ADMIN:
            admin_count = await self.users.count_by_role(UserRole.ADMIN)
            if admin_count <= 1:
                raise PermissionDeniedError("Cannot demote the last admin")

        user.role = payload.role
        await self.session.commit()
        return user

    async def delete(self, user_id: int, actor: User) -> None:
        if user_id == actor.id:
            raise PermissionDeniedError("You cannot delete your own account")

        user = await self.get(user_id)

        await self.users.delete(user)
        await self.session.commit()
