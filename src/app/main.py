from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.router import api_router
from app.db.session import engine, get_db
from app.exceptions import (
    AppError,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    NotFoundError,
    PermissionDeniedError,
)

ERROR_STATUS: dict[type[AppError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    EmailAlreadyExistsError: status.HTTP_409_CONFLICT,
    InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
    PermissionDeniedError: status.HTTP_403_FORBIDDEN,
}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    application = FastAPI(title="Chancery API", lifespan=lifespan)

    @application.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=ERROR_STATUS.get(type(exc), status.HTTP_400_BAD_REQUEST),
            content={"detail": str(exc)},
        )

    application.include_router(api_router)

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/health/db")
    async def health_db(session: Annotated[AsyncSession, Depends(get_db)]) -> dict[str, str]:
        await session.execute(text("SELECT 1;"))
        return {"status": "ok"}

    return application


app = create_app()
