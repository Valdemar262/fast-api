from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from collections.abc import Awaitable, Callable

from app.core.security import ACCESS_TOKEN_TYPE, decode_token
from app.db.session import get_db
from app.enums import UserRole
from app.models import User
from app.repositories.user import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

DbSession = Annotated[AsyncSession, Depends(get_db)]
AccessToken = Annotated[str, Depends(oauth2_scheme)]


async def get_current_user(session: DbSession, token: AccessToken) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token, ACCESS_TOKEN_TYPE)
    except jwt.InvalidTokenError:
        raise credentials_error from None

    user = await UserRepository(session).get_by_id(int(payload["sub"]))

    if user is None:
        raise credentials_error

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: UserRole) -> Callable[[User], Awaitable[User]]:
    async def checker(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return user

    return checker
