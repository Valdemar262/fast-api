from fastapi import APIRouter

from app.api.v1.endpoints import auth, booking, reports, resources, statement, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(resources.router)
api_router.include_router(booking.router)
api_router.include_router(statement.router)
api_router.include_router(users.router)
api_router.include_router(reports.router)
