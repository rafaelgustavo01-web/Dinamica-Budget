from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse, UsuarioCreate, UsuarioResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(UsuarioRepository(db))


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
    svc: AuthService = Depends(_get_auth_service),
) -> TokenResponse:
    return await svc.login(credentials, db)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    svc: AuthService = Depends(_get_auth_service),
) -> TokenResponse:
    return await svc.refresh_token(request.refresh_token, db)


@router.post("/logout", status_code=204)
async def logout(
    current_user=Depends(get_current_active_user),
    svc: AuthService = Depends(_get_auth_service),
) -> None:
    await svc.logout(current_user.id)


@router.post("/usuarios", response_model=UsuarioResponse, status_code=201)
async def create_usuario(
    data: UsuarioCreate,
    svc: AuthService = Depends(_get_auth_service),
) -> UsuarioResponse:
    user = await svc.create_user(data)
    return UsuarioResponse.model_validate(user)
