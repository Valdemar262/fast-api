from fastapi import APIRouter

from app.api.v1.endpoints import auth, booking, resources

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(resources.router)
api_router.include_router(booking.router)