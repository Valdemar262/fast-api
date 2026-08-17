import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.exceptions import EmailAlreadyExistsError, InvalidCredentialsError
from app.models import User
from app.repositories.user import UserRepository
from app.schemas import TokenPair, UserCreate


def _issue_tokens(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user = UserRepository(session)

    async def register(self, payload: UserCreate) -> tuple[User, TokenPair]:
        existing = await self.user.get_by_email(payload.email)

        if existing is not None:
            raise EmailAlreadyExistsError(f"Email {payload.email} is already registered")

        user = await self.user.create(
            **payload.model_dump(exclude={"password"}),
            password_hash=hash_password(payload.password)
        )

        await self.session.commit()

        return user, _issue_tokens(user)

    async def login(self, email: str, password: str) -> tuple[User, TokenPair]:
        user = await self.user.get_by_email(email)

        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        return user, _issue_tokens(user)

    async def refresh(self, refresh_token: str) -> TokenPair:
        try:
            payload = decode_token(refresh_token, REFRESH_TOKEN_TYPE)
        except jwt.InvalidTokenError as exc:
            raise InvalidCredentialsError("Invalid refresh token") from exc

        user_id = int(payload["sub"])
        user = await self.user.get_by_id(user_id)

        if user is None:
            raise InvalidCredentialsError("User not found")

        return _issue_tokens(user)
