from collections.abc import Awaitable, Callable
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache
from app.core.security import ACCESS_TOKEN_TYPE, decode_token
from app.db.session import get_db
from app.enums import UserRole
from app.models import User
from app.repositories.user import UserRepository
from app.services.booking import BookingService
from app.services.report import ReportService
from app.services.resource import ResourceService
from app.services.statement import StatementService
from app.services.user import UserService

bearer_scheme = HTTPBearer()

DbSession = Annotated[AsyncSession, Depends(get_db)]
AccessToken = Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)]


async def get_current_user(session: DbSession, credentials: AccessToken) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(credentials.credentials, ACCESS_TOKEN_TYPE)
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


def get_resource_service(session: DbSession) -> ResourceService:
    return ResourceService(session, cache)


def get_booking_service(session: DbSession) -> BookingService:
    return BookingService(session)


def get_statement_service(session: DbSession) -> StatementService:
    return StatementService(session)


def get_report_service(session: DbSession) -> ReportService:
    return ReportService(session)


def get_user_service(session: DbSession) -> UserService:
    return UserService(session)


ResourceServiceDep = Annotated[ResourceService, Depends(get_resource_service)]
BookingServiceDep = Annotated[BookingService, Depends(get_booking_service)]
StatementServiceDep = Annotated[StatementService, Depends(get_statement_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]
