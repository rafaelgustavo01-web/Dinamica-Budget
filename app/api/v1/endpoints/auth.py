from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.core.dependencies import get_current_active_user, get_db
from app.models.usuario import UsuarioPerfil
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.auth import (
    LoginRequest,
    MeResponse,
    PerfilClienteResponse,
    RefreshRequest,
    TokenResponse,
    UsuarioCreate,
    UsuarioResponse,
)
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


@router.get("/me", response_model=MeResponse)
async def me(
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MeResponse:
    """Returns current user with all client/perfil bindings."""
    result = await db.execute(
        select(UsuarioPerfil).where(UsuarioPerfil.usuario_id == current_user.id)
    )
    perfis_db = result.scalars().all()
    perfis = [
        PerfilClienteResponse(cliente_id=str(p.cliente_id), perfil=p.perfil)
        for p in perfis_db
    ]
    if current_user.is_admin:
        perfis.append(PerfilClienteResponse(cliente_id="*", perfil="ADMIN"))
    return MeResponse(
        id=str(current_user.id),
        nome=current_user.nome,
        email=current_user.email,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin,
        perfis=perfis,
    )


@router.post("/usuarios", response_model=UsuarioResponse, status_code=201)
async def create_usuario(
    data: UsuarioCreate,
    svc: AuthService = Depends(_get_auth_service),
) -> UsuarioResponse:
    user = await svc.create_user(data)
    return UsuarioResponse.model_validate(user)
