from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine, get_db

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield
    await engine.dispose()

def create_app() -> FastAPI:
    application = FastAPI(title="Chancery API", lifespan=lifespan)

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/health/db")
    async def health_db(session: AsyncSession = Depends(get_db)) -> dict[str, str]:
        await session.execute(text("SELECT 1;"))
        return {"status": "ok"}

    return application

app = create_app()
