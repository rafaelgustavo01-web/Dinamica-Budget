from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usuario import Usuario
from app.repositories.base_repository import BaseRepository


class UsuarioRepository(BaseRepository[Usuario]):
    model = Usuario

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def get_by_email(self, email: str) -> Usuario | None:
        result = await self.db.execute(
            select(Usuario).where(Usuario.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, id: UUID) -> Usuario | None:  # type: ignore[override]
        result = await self.db.execute(select(Usuario).where(Usuario.id == id))
        return result.scalar_one_or_none()

    async def update_refresh_token(self, user_id: UUID, token_hash: str | None) -> None:
        user = await self.get_by_id(user_id)
        if user:
            user.refresh_token_hash = token_hash
            await self.db.flush()
