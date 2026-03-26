import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.historico_busca_cliente import HistoricoBuscaCliente
from app.repositories.base_repository import BaseRepository


class HistoricoRepository(BaseRepository[HistoricoBuscaCliente]):
    model = HistoricoBuscaCliente

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def create_registro(
        self,
        cliente_id: UUID,
        texto_busca: str,
        usuario_origem: str,
    ) -> HistoricoBuscaCliente:
        registro = HistoricoBuscaCliente(
            id=uuid.uuid4(),
            cliente_id=cliente_id,
            texto_busca=texto_busca,
            usuario_origem=usuario_origem,
        )
        self.db.add(registro)
        await self.db.flush()
        await self.db.refresh(registro)
        return registro

    async def get_by_id(self, id: UUID) -> HistoricoBuscaCliente | None:  # type: ignore[override]
        result = await self.db.execute(
            select(HistoricoBuscaCliente).where(HistoricoBuscaCliente.id == id)
        )
        return result.scalar_one_or_none()
