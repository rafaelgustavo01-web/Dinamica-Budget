import math
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.composicao_tcpo import ComposicaoTcpo
from app.models.enums import OrigemItem, StatusHomologacao
from app.models.servico_tcpo import ServicoTcpo
from app.repositories.servico_tcpo_repository import ServicoTcpoRepository
from app.schemas.common import PaginatedResponse
from app.schemas.servico import (
    ComposicaoItemResponse,
    ExplodeComposicaoResponse,
    ServicoCreate,
    ServicoListParams,
    ServicoTcpoResponse,
)
from app.services.embedding_sync_service import embedding_sync_service

logger = get_logger(__name__)


class ServicoCatalogService:

    # ─── Listing / Get ────────────────────────────────────────────────────────

    async def list_servicos(
        self,
        params: ServicoListParams,
        db: AsyncSession,
    ) -> PaginatedResponse[ServicoTcpoResponse]:
        repo = ServicoTcpoRepository(db)
        offset = (params.page - 1) * params.page_size
        items, total = await repo.list_paginated(
            q=params.q,
            categoria_id=params.categoria_id,
            offset=offset,
            limit=params.page_size,
        )
        pages = math.ceil(total / params.page_size) if total else 0
        return PaginatedResponse(
            items=[ServicoTcpoResponse.model_validate(s) for s in items],
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=pages,
        )

    async def get_servico(self, servico_id: UUID, db: AsyncSession) -> ServicoTcpoResponse:
        repo = ServicoTcpoRepository(db)
        servico = await repo.get_active_by_id(servico_id)
        if not servico:
            raise NotFoundError("ServicoTcpo", str(servico_id))
        return ServicoTcpoResponse.model_validate(servico)

    # ─── Composição Explosion ─────────────────────────────────────────────────

    async def explode_composicao(
        self, servico_id: UUID, db: AsyncSession
    ) -> ExplodeComposicaoResponse:
        repo = ServicoTcpoRepository(db)
        servico = await repo.get_with_composicao(servico_id)
        if not servico:
            raise NotFoundError("ServicoTcpo", str(servico_id))

        itens = []
        custo_total = Decimal("0")

        for comp in servico.composicoes_pai:
            filho = comp.insumo_filho
            custo_item = comp.quantidade_consumo * filho.custo_unitario
            custo_total += custo_item
            itens.append(
                ComposicaoItemResponse(
                    id=comp.id,
                    insumo_filho_id=filho.id,
                    descricao_filho=filho.descricao,
                    unidade_medida=filho.unidade_medida,
                    quantidade_consumo=comp.quantidade_consumo,
                    custo_unitario=filho.custo_unitario,
                    custo_total=custo_item,
                )
            )

        return ExplodeComposicaoResponse(
            servico=ServicoTcpoResponse.model_validate(servico),
            itens=itens,
            custo_total_composicao=custo_total,
        )

    # ─── Anti-Loop Validation ─────────────────────────────────────────────────

    async def _detectar_ciclo(
        self,
        pai_id: UUID,
        filho_id: UUID,
        db: AsyncSession,
    ) -> bool:
        """
        DFS to detect circular references before inserting a composition.
        Returns True if adding (pai_id → filho_id) would create a cycle.

        A cycle exists if filho_id is an ancestor of pai_id,
        i.e., pai_id can be reached from filho_id via existing compositions.
        """
        # Build a descendant set of filho_id — if pai_id is in it, it's a cycle
        visited: set[UUID] = set()
        queue: list[UUID] = [filho_id]

        while queue:
            current = queue.pop()
            if current == pai_id:
                return True  # cycle detected
            if current in visited:
                continue
            visited.add(current)

            # Find all children of current
            result = await db.execute(
                select(ComposicaoTcpo.insumo_filho_id).where(
                    ComposicaoTcpo.servico_pai_id == current
                )
            )
            for (child_id,) in result.fetchall():
                queue.append(child_id)

        # Also check self-reference
        if pai_id == filho_id:
            return True

        return False

    async def adicionar_composicao(
        self,
        pai_id: UUID,
        filho_id: UUID,
        quantidade_consumo: Decimal,
        db: AsyncSession,
    ) -> ComposicaoTcpo:
        """
        Add a composition item with anti-loop guard.
        Raises ValidationError if the addition would create a circular reference.
        """
        repo = ServicoTcpoRepository(db)

        pai = await repo.get_active_by_id(pai_id)
        if not pai:
            raise NotFoundError("ServicoTcpo (pai)", str(pai_id))
        filho = await repo.get_active_by_id(filho_id)
        if not filho:
            raise NotFoundError("ServicoTcpo (filho)", str(filho_id))

        if await self._detectar_ciclo(pai_id, filho_id, db):
            raise ValidationError(
                f"Referência circular detectada: adicionar '{filho.descricao}' "
                f"a '{pai.descricao}' criaria um loop na composição."
            )

        comp = ComposicaoTcpo(
            id=uuid.uuid4(),
            servico_pai_id=pai_id,
            insumo_filho_id=filho_id,
            quantidade_consumo=quantidade_consumo,
        )
        db.add(comp)
        await db.flush()

        logger.info(
            "composicao_adicionada",
            pai_id=str(pai_id),
            filho_id=str(filho_id),
            qtd=str(quantidade_consumo),
        )
        return comp

    # ─── Price Roll-up ────────────────────────────────────────────────────────

    async def recalcular_custo_pai(
        self, filho_id: UUID, db: AsyncSession
    ) -> list[UUID]:
        """
        When a child's custo_unitario changes, recalculate all parent services
        that include this child in their composition.
        Returns list of updated parent IDs.

        Note: This updates custo_unitario of the PAI based on sum of its
        composicao children — only for PROPRIA items (TCPO prices are immutable).
        """
        # Find all parents that contain filho_id
        result = await db.execute(
            select(ComposicaoTcpo).where(ComposicaoTcpo.insumo_filho_id == filho_id)
        )
        compositions = list(result.scalars().all())

        updated_pais: list[UUID] = []

        for comp in compositions:
            pai = await db.get(ServicoTcpo, comp.servico_pai_id)
            if not pai or pai.origem != OrigemItem.PROPRIA:
                continue  # never overwrite TCPO catalog prices

            # Reload all children of this parent to compute sum
            all_children_result = await db.execute(
                select(ComposicaoTcpo).where(ComposicaoTcpo.servico_pai_id == pai.id)
            )
            all_children = list(all_children_result.scalars().all())

            total = Decimal("0")
            for child_comp in all_children:
                filho = await db.get(ServicoTcpo, child_comp.insumo_filho_id)
                if filho:
                    total += child_comp.quantidade_consumo * filho.custo_unitario

            if total != pai.custo_unitario:
                old_val = pai.custo_unitario
                pai.custo_unitario = total
                await db.flush()
                updated_pais.append(pai.id)
                logger.info(
                    "preco_pai_atualizado",
                    pai_id=str(pai.id),
                    old=float(old_val),
                    new=float(total),
                )

        return updated_pais

    # ─── Create / Delete ──────────────────────────────────────────────────────

    async def create_servico(
        self, data: ServicoCreate, db: AsyncSession
    ) -> ServicoTcpoResponse:
        repo = ServicoTcpoRepository(db)
        servico = ServicoTcpo(
            id=uuid.uuid4(),
            codigo_origem=data.codigo_origem,
            descricao=data.descricao,
            unidade_medida=data.unidade_medida,
            custo_unitario=data.custo_unitario,
            categoria_id=data.categoria_id,
            origem=OrigemItem.TCPO,
            status_homologacao=StatusHomologacao.APROVADO,
        )
        servico = await repo.create(servico)
        await embedding_sync_service.sync_create_or_update(servico.id, db)
        logger.info("servico_tcpo_created", id=str(servico.id))
        return ServicoTcpoResponse.model_validate(servico)

    async def soft_delete_servico(self, servico_id: UUID, db: AsyncSession) -> None:
        repo = ServicoTcpoRepository(db)
        servico = await repo.get_active_by_id(servico_id)
        if not servico:
            raise NotFoundError("ServicoTcpo", str(servico_id))
        servico.deleted_at = datetime.now(UTC)
        await repo.update(servico)
        await embedding_sync_service.sync_delete(servico_id, db)

    async def compute_all_embeddings(self, db: AsyncSession) -> int:
        return await embedding_sync_service.compute_all_missing(db)


servico_catalog_service = ServicoCatalogService()
