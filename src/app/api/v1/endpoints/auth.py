from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas import AuthResponse, LoginRequest, RefreshRequest, TokenPair, UserCreate, UserRead
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, session: DbSession) -> AuthResponse:
    user, tokens = await AuthService(session).register(payload)
    return AuthResponse(user=UserRead.model_validate(user), tokens=tokens)


@router.post("/login", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def login(payload: LoginRequest, session: DbSession) -> AuthResponse:
    user, tokens = await AuthService(session).login(payload.email, payload.password)
    return AuthResponse(user=UserRead.model_validate(user), tokens=tokens)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, session: DbSession) -> TokenPair:
    tokens = await AuthService(session).refresh(payload.refresh_token)
    return tokens


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
