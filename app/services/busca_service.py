"""
Motor de Busca em Cascata — V2

Fluxo:
  Fase 0 (Itens Próprios): Busca pg_trgm restrita a itens PROPRIA do cliente com status APROVADO
  Fase 1 (Associação Direta): Lookup em associacao_inteligente com cliente_id + texto normalizado
                               → se CONSOLIDADA: circuit break imediato
                               → se VALIDADA/SUGERIDA: retorna e fortalece
  Fase 2 (Fuzzy Global): pg_trgm sobre catálogo global (TCPO APROVADO)
  Fase 3 (IA Semântica): pgvector cosine similarity

Normalização obrigatória em todas as fases:
  strip → lowercase → remoção de acentos → collapse whitespace

Histórico gravado via BackgroundTask (não bloqueia response).
"""

import time
import uuid
from decimal import Decimal
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.ml.embedder import embedder
from app.ml.vector_search import vector_searcher
from app.models.associacao_inteligente import CONSOLIDACAO_THRESHOLD
from app.models.enums import OrigemAssociacao, OrigemItem, StatusHomologacao, StatusValidacaoAssociacao
from app.repositories.associacao_repository import AssociacaoRepository, normalize_text
from app.repositories.historico_repository import HistoricoRepository
from app.repositories.servico_tcpo_repository import ServicoTcpoRepository
from app.schemas.busca import (
    AssociacaoResponse,
    BuscaServicoRequest,
    BuscaServicoResponse,
    CriarAssociacaoRequest,
    ResultadoBusca,
)

logger = get_logger(__name__)


class BuscaService:

    async def buscar(
        self,
        request: BuscaServicoRequest,
        usuario_email: str,
        db: AsyncSession,
        background_tasks: BackgroundTasks,
    ) -> BuscaServicoResponse:
        t0 = time.monotonic()

        # ── Normalização obrigatória ──────────────────────────────────────────
        texto_norm = normalize_text(request.texto_busca)

        assoc_repo = AssociacaoRepository(db)
        servico_repo = ServicoTcpoRepository(db)

        # ─────────────────────────────────────────────────────────────────────
        # FASE 0: Itens Próprios do Cliente (PROPRIA + APROVADO)
        # Prioriza o portfólio homologado do cliente antes do catálogo global
        # ─────────────────────────────────────────────────────────────────────
        resultado = await self._fase0_itens_proprios(
            cliente_id=request.cliente_id,
            texto_norm=texto_norm,
            threshold=request.threshold_score,
            limit=request.limite_resultados,
            servico_repo=servico_repo,
        )
        if resultado:
            return await self._build_response(
                texto_busca=request.texto_busca,
                resultados=resultado,
                t0=t0,
                cliente_id=request.cliente_id,
                usuario_email=usuario_email,
                background_tasks=background_tasks,
                db=db,
            )

        # ─────────────────────────────────────────────────────────────────────
        # FASE 1: Associação Direta (associacao_inteligente)
        # ─────────────────────────────────────────────────────────────────────
        resultado, associacao = await self._fase1_associacao(
            cliente_id=request.cliente_id,
            texto_norm=texto_norm,
            assoc_repo=assoc_repo,
            servico_repo=servico_repo,
        )
        if resultado:
            # Fortalecer associação usada (async — dentro da mesma sessão)
            if associacao:
                await assoc_repo.fortalecer(associacao)
            return await self._build_response(
                texto_busca=request.texto_busca,
                resultados=resultado,
                t0=t0,
                cliente_id=request.cliente_id,
                usuario_email=usuario_email,
                background_tasks=background_tasks,
                db=db,
            )

        # ─────────────────────────────────────────────────────────────────────
        # FASE 2: Fuzzy Global (pg_trgm — catálogo TCPO APROVADO)
        # ─────────────────────────────────────────────────────────────────────
        resultado = await self._fase2_fuzzy(
            texto_busca=texto_norm,
            threshold=request.threshold_score,
            limit=request.limite_resultados,
            servico_repo=servico_repo,
        )
        if resultado:
            return await self._build_response(
                texto_busca=request.texto_busca,
                resultados=resultado,
                t0=t0,
                cliente_id=request.cliente_id,
                usuario_email=usuario_email,
                background_tasks=background_tasks,
                db=db,
            )

        # ─────────────────────────────────────────────────────────────────────
        # FASE 3: IA Semântica (pgvector)
        # ─────────────────────────────────────────────────────────────────────
        resultado = await self._fase3_semantica(
            texto_busca=texto_norm,
            threshold=request.threshold_score,
            limit=request.limite_resultados,
            db=db,
            servico_repo=servico_repo,
        )

        return await self._build_response(
            texto_busca=request.texto_busca,
            resultados=resultado,
            t0=t0,
            cliente_id=request.cliente_id,
            usuario_email=usuario_email,
            background_tasks=background_tasks,
            db=db,
        )

    # ─── Fase 0: Itens Próprios do Cliente ───────────────────────────────────

    async def _fase0_itens_proprios(
        self,
        cliente_id: UUID,
        texto_norm: str,
        threshold: float,
        limit: int,
        servico_repo: ServicoTcpoRepository,
    ) -> list[ResultadoBusca] | None:
        rows = await servico_repo.fuzzy_search_scoped(
            texto_busca=texto_norm,
            threshold=threshold,
            limit=limit,
            cliente_id=cliente_id,
            origem=OrigemItem.PROPRIA,
            status_homologacao=StatusHomologacao.APROVADO,
        )
        if not rows:
            return None

        logger.info("fase0_proprios_hit", cliente_id=str(cliente_id), count=len(rows))
        return [
            ResultadoBusca(
                id_tcpo=s.id,
                codigo_origem=s.codigo_origem,
                descricao=s.descricao,
                unidade=s.unidade_medida,
                custo_unitario=float(s.custo_unitario),
                score=round(score, 4),
                score_confianca=round(score, 4),
                origem_match="PROPRIA_CLIENTE",
                status_homologacao=s.status_homologacao.value,
            )
            for s, score in rows
        ]

    # ─── Fase 1: Associação Direta ────────────────────────────────────────────

    async def _fase1_associacao(
        self,
        cliente_id: UUID,
        texto_norm: str,
        assoc_repo: AssociacaoRepository,
        servico_repo: ServicoTcpoRepository,
    ) -> tuple[list[ResultadoBusca] | None, object]:
        assoc = await assoc_repo.find_by_cliente_and_text(
            cliente_id=cliente_id,
            texto_normalizado=texto_norm,
        )
        if not assoc:
            return None, None

        servico = await servico_repo.get_active_by_id(assoc.servico_tcpo_id)
        if not servico:
            return None, None

        # Only auto-return immediately for CONSOLIDADA associations
        if assoc.status_validacao != StatusValidacaoAssociacao.CONSOLIDADA:
            logger.info(
                "fase1_associacao_validada",
                status=assoc.status_validacao,
                freq=assoc.frequencia_uso,
            )
        else:
            logger.info("fase1_consolidada_circuit_break", servico_id=str(servico.id))

        return [
            ResultadoBusca(
                id_tcpo=servico.id,
                codigo_origem=servico.codigo_origem,
                descricao=servico.descricao,
                unidade=servico.unidade_medida,
                custo_unitario=float(servico.custo_unitario),
                score=1.0,
                score_confianca=float(assoc.confiabilidade_score or 1.0),
                origem_match="ASSOCIACAO_DIRETA",
                status_homologacao=servico.status_homologacao.value,
            )
        ], assoc

    # ─── Fase 2: Fuzzy Global ─────────────────────────────────────────────────

    async def _fase2_fuzzy(
        self,
        texto_busca: str,
        threshold: float,
        limit: int,
        servico_repo: ServicoTcpoRepository,
    ) -> list[ResultadoBusca] | None:
        rows = await servico_repo.fuzzy_search_scoped(
            texto_busca=texto_busca,
            threshold=threshold,
            limit=limit,
            cliente_id=None,  # global catalog
            origem=OrigemItem.TCPO,
            status_homologacao=StatusHomologacao.APROVADO,
        )
        if not rows:
            return None

        logger.info("fase2_fuzzy_hit", count=len(rows))
        return [
            ResultadoBusca(
                id_tcpo=s.id,
                codigo_origem=s.codigo_origem,
                descricao=s.descricao,
                unidade=s.unidade_medida,
                custo_unitario=float(s.custo_unitario),
                score=round(score, 4),
                score_confianca=round(score, 4),
                origem_match="FUZZY",
                status_homologacao=s.status_homologacao.value,
            )
            for s, score in rows
        ]

    # ─── Fase 3: IA Semântica ─────────────────────────────────────────────────

    async def _fase3_semantica(
        self,
        texto_busca: str,
        threshold: float,
        limit: int,
        db: AsyncSession,
        servico_repo: ServicoTcpoRepository,
    ) -> list[ResultadoBusca]:
        if not embedder.ready:
            logger.warning("fase3_skipped_embedder_not_ready")
            return []

        query_vector = embedder.encode(texto_busca)
        candidates = await vector_searcher.search(
            query_vector=query_vector,
            db=db,
            threshold=threshold,
            limit=limit,
        )

        results = []
        for servico_id, score, metadata in candidates:
            servico = await servico_repo.get_active_by_id(servico_id)
            if not servico:
                continue
            # Only return approved items
            if servico.status_homologacao != StatusHomologacao.APROVADO:
                continue
            results.append(
                ResultadoBusca(
                    id_tcpo=servico.id,
                    codigo_origem=servico.codigo_origem,
                    descricao=servico.descricao,
                    unidade=servico.unidade_medida,
                    custo_unitario=float(servico.custo_unitario),
                    score=round(score, 4),
                    score_confianca=round(score, 4),
                    origem_match="IA_SEMANTICA",
                    status_homologacao=servico.status_homologacao.value,
                )
            )

        logger.info("fase3_semantica_hit", count=len(results))
        return results

    # ─── Helpers ──────────────────────────────────────────────────────────────

    async def _build_response(
        self,
        texto_busca: str,
        resultados: list[ResultadoBusca],
        t0: float,
        cliente_id: UUID,
        usuario_email: str,
        background_tasks: BackgroundTasks,
        db: AsyncSession,
    ) -> BuscaServicoResponse:
        elapsed = int((time.monotonic() - t0) * 1000)
        historico_id = str(uuid.uuid4())

        async def _gravar():
            from app.core.database import get_db_session

            async for session in get_db_session():
                repo = HistoricoRepository(session)
                await repo.create_registro(
                    cliente_id=cliente_id,
                    texto_busca=texto_busca,
                    usuario_origem=usuario_email,
                )

        background_tasks.add_task(_gravar)

        return BuscaServicoResponse(
            texto_buscado=texto_busca,
            resultados=resultados,
            metadados={
                "tempo_processamento_ms": elapsed,
                "id_historico_busca": historico_id,
            },
        )

    # ─── Criar Associação ─────────────────────────────────────────────────────

    async def criar_associacao(
        self,
        request: CriarAssociacaoRequest,
        usuario_email: str,
        db: AsyncSession,
    ) -> AssociacaoResponse:
        servico_repo = ServicoTcpoRepository(db)
        assoc_repo = AssociacaoRepository(db)

        servico = await servico_repo.get_active_by_id(request.id_tcpo_selecionado)
        if not servico:
            raise NotFoundError("ServicoTcpo", str(request.id_tcpo_selecionado))

        # Sanitize before upsert
        associacao = await assoc_repo.upsert_associacao(
            cliente_id=request.cliente_id,
            texto_busca_original=request.texto_busca_original,
            servico_tcpo_id=request.id_tcpo_selecionado,
            origem=OrigemAssociacao.MANUAL_USUARIO,
            confiabilidade_score=Decimal("1.00"),
        )

        logger.info(
            "associacao_criada_ou_fortalecida",
            id=str(associacao.id),
            freq=associacao.frequencia_uso,
            status=associacao.status_validacao,
        )

        return AssociacaoResponse(
            status="ok",
            mensagem=f"Associação {associacao.status_validacao.value} (frequência: {associacao.frequencia_uso}).",
            id_associacao=associacao.id,
        )


busca_service = BuscaService()
