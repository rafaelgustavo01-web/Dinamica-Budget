from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    # Import here to avoid circular imports
    from app.repositories.usuario_repository import UsuarioRepository
    from uuid import UUID

    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise AuthenticationError(str(exc)) from exc

    if payload.get("type") != "access":
        raise AuthenticationError("Tipo de token inválido.")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationError("Token sem identificador de usuário.")

    repo = UsuarioRepository(db)
    user = await repo.get_by_id(UUID(user_id_str))
    if not user:
        raise AuthenticationError("Usuário não encontrado.")
    return user


async def get_current_active_user(current_user=Depends(get_current_user)):
    if not current_user.is_active:
        raise AuthorizationError("Usuário inativo.")
    return current_user


async def get_current_admin_user(current_user=Depends(get_current_active_user)):
    if not current_user.is_admin:
        raise AuthorizationError("Acesso restrito a administradores.")
    return current_user
