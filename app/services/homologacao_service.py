"""
Homologation workflow service.

Manages the lifecycle of PROPRIA items:
  PENDENTE → APROVADO  (via POST /homologacao/aprovar with approved=True)
  PENDENTE → REPROVADO (via POST /homologacao/aprovar with approved=False)

Business rules:
  - Only users with APROVADOR or ADMIN perfil can approve/reject items.
  - When approved, embedding is synced automatically.
  - When rejected, item is kept (for audit) but never shown in search results.
  - All status changes are captured by SQLAlchemy audit hooks.
"""

import math
import uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.enums import OrigemItem, PerfilUsuario, StatusHomologacao
from app.models.servico_tcpo import ServicoTcpo
from app.repositories.servico_tcpo_repository import ServicoTcpoRepository
from app.schemas.common import PaginatedResponse
from app.schemas.homologacao import (
    AprovarHomologacaoRequest,
    AprovarHomologacaoResponse,
    CriarItemProprioRequest,
    ItemPendenteResponse,
)
from app.services.embedding_sync_service import embedding_sync_service

logger = get_logger(__name__)


class HomologacaoService:

    async def listar_pendentes(
        self,
        cliente_id: UUID,
        page: int,
        page_size: int,
        db: AsyncSession,
    ) -> PaginatedResponse[ItemPendenteResponse]:
        repo = ServicoTcpoRepository(db)
        offset = (page - 1) * page_size
        items, total = await repo.list_pendentes_homologacao(
            cliente_id=cliente_id, offset=offset, limit=page_size
        )
        pages = math.ceil(total / page_size) if total else 0
        return PaginatedResponse(
            items=[ItemPendenteResponse.model_validate(s) for s in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def aprovar(
        self,
        request: AprovarHomologacaoRequest,
        aprovador_email: str,
        aprovador_id: UUID,
        aprovador_perfis: list[str],
        db: AsyncSession,
    ) -> AprovarHomologacaoResponse:
        # RBAC check
        allowed = {PerfilUsuario.APROVADOR.value, PerfilUsuario.ADMIN.value}
        if not any(p in allowed for p in aprovador_perfis):
            raise AuthorizationError(
                "Somente usuários com perfil APROVADOR ou ADMIN podem homologar itens."
            )

        repo = ServicoTcpoRepository(db)
        servico = await repo.get_active_by_id(request.servico_id)
        if not servico:
            raise NotFoundError("ServicoTcpo", str(request.servico_id))

        if servico.status_homologacao != StatusHomologacao.PENDENTE:
            raise ValidationError(
                f"Item já processado com status '{servico.status_homologacao.value}'."
            )

        now = datetime.now(UTC)

        if request.aprovado:
            servico.status_homologacao = StatusHomologacao.APROVADO
            servico.aprovado_por_id = aprovador_id
            servico.data_aprovacao = now
            # Sync embedding now that item is approved
            await embedding_sync_service.sync_create_or_update(servico.id, db)
            mensagem = "Item homologado e disponível para busca."
            logger.info("item_aprovado", servico_id=str(servico.id), by=aprovador_email)
        else:
            servico.status_homologacao = StatusHomologacao.REPROVADO
            servico.aprovado_por_id = aprovador_id
            servico.data_aprovacao = now
            mensagem = f"Item reprovado. Motivo: {request.motivo_reprovacao or 'não informado'}."
            logger.info("item_reprovado", servico_id=str(servico.id), by=aprovador_email)

        await repo.update(servico)

        return AprovarHomologacaoResponse(
            servico_id=servico.id,
            status_homologacao=servico.status_homologacao.value,
            aprovado_por=aprovador_email,
            data_aprovacao=now,
            mensagem=mensagem,
        )

    async def criar_item_proprio(
        self,
        request: CriarItemProprioRequest,
        db: AsyncSession,
    ) -> ServicoTcpo:
        """
        Creates a PROPRIA item for a client starting with PENDENTE status.
        Does NOT sync embeddings yet — only synced after approval.
        """
        repo = ServicoTcpoRepository(db)
        servico = ServicoTcpo(
            id=uuid.uuid4(),
            cliente_id=request.cliente_id,
            codigo_origem=request.codigo_origem,
            descricao=request.descricao,
            unidade_medida=request.unidade_medida,
            custo_unitario=request.custo_unitario,
            categoria_id=request.categoria_id,
            origem=OrigemItem.PROPRIA,
            status_homologacao=StatusHomologacao.PENDENTE,
        )
        return await repo.create(servico)


homologacao_service = HomologacaoService()
