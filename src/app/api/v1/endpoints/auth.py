from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.exceptions import EmailAlreadyExistsError, InvalidCredentialsError
from app.schemas import AuthResponse, LoginRequest, RefreshRequest, TokenPair, UserCreate, UserRead
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, session: DbSession) -> AuthResponse:
    try:
        user, tokens = await AuthService(session).register(payload)
    except EmailAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return AuthResponse(user=UserRead.model_validate(user), tokens=tokens)


@router.post("/login", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def login(payload: LoginRequest, session: DbSession) -> AuthResponse:
    try:
        user, tokens = await AuthService(session).login(payload.email, payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return AuthResponse(user=UserRead.model_validate(user), tokens=tokens)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, session: DbSession) -> TokenPair:
    try:
        tokens = await AuthService(session).refresh(payload.refresh_token)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return tokens


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
