import logging
import time
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.router import api_router
from app.core.log_config import configure_logging
from app.db.session import engine, get_db
from app.exceptions import (
    AppError,
    BookingConflictError,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidStatusTransitionError,
    NotFoundError,
    PermissionDeniedError,
)

logger = logging.getLogger(__name__)

DESCRIPTION = """
Resource booking and approval workflow.

Clients create statements, submit them for review and book resources;
administrators approve or reject statements, manage resources and users, and
download CSV reports.

Authentication is a JWT bearer token: call `POST /api/v1/auth/login`, then use
**Authorize** with the returned `access_token`.
"""

TAGS_METADATA = [
    {
        "name": "auth",
        "description": "Registration, login, token refresh and the current user.",
    },
    {
        "name": "users",
        "description": "User administration. Listing and role changes are admin-only.",
    },
    {
        "name": "resources",
        "description": (
            "Bookable resources. Any authenticated user may read them; "
            "creating, updating and deleting is admin-only."
        ),
    },
    {
        "name": "bookings",
        "description": "Time-range bookings for a resource, with overlap detection.",
    },
    {
        "name": "statements",
        "description": "Statements and their draft → submitted → approved/rejected workflow.",
    },
    {"name": "reports", "description": "Aggregate CSV reports. Admin-only."},
    {"name": "health", "description": "Liveness probes."},
]

ERROR_STATUS: dict[type[AppError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    EmailAlreadyExistsError: status.HTTP_409_CONFLICT,
    InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
    PermissionDeniedError: status.HTTP_403_FORBIDDEN,
    BookingConflictError: status.HTTP_409_CONFLICT,
    InvalidStatusTransitionError: status.HTTP_409_CONFLICT,
}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    logger.info("Application started")
    yield
    await engine.dispose()
    logger.info("Application stopped, database connections released")


def create_app() -> FastAPI:
    application = FastAPI(
        title="Chancery API",
        description=DESCRIPTION,
        version="1.0.0",
        openapi_tags=TAGS_METADATA,
        lifespan=lifespan,
    )

    @application.middleware("http")
    async def log_requests(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        started = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - started

        logger.info(
            "%s %s → %s in %.3fs",
            request.method,
            request.url.path,
            response.status_code,
            duration,
        )
        return response

    @application.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        status_code = ERROR_STATUS[type(exc)]
        logger.warning("%s on %s: %s", type(exc).__name__, request.url.path, exc)

        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

    application.include_router(api_router)

    @application.get("/health", tags=["health"], summary="Liveness probe")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get(
        "/health/db",
        tags=["health"],
        summary="Liveness probe including the database",
    )
    async def health_db(session: Annotated[AsyncSession, Depends(get_db)]) -> dict[str, str]:
        await session.execute(text("SELECT 1;"))
        return {"status": "ok"}

    return application


app = create_app()
