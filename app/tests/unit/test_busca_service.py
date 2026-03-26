"""Unit tests for the 3-layer search cascade."""

import re
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.busca_service import _normalize


def test_normalize_strips_and_lowercases():
    assert _normalize("  Escavação   MANUAL  ") == "escavação manual"


def test_normalize_collapses_whitespace():
    assert _normalize("concreto   fck  25") == "concreto fck 25"


@pytest.mark.asyncio
async def test_fase1_returns_result_when_association_found():
    from app.schemas.busca import ResultadoBusca
    from app.services.busca_service import BuscaService

    mock_assoc = MagicMock()
    mock_assoc.servico_tcpo_id = uuid.uuid4()

    mock_servico = MagicMock()
    mock_servico.id = mock_assoc.servico_tcpo_id
    mock_servico.codigo_origem = "01.001.001"
    mock_servico.descricao = "Escavação manual de valas"
    mock_servico.unidade_medida = "m³"
    mock_servico.custo_unitario = 45.50

    assoc_repo = AsyncMock()
    assoc_repo.find_by_cliente_and_text = AsyncMock(return_value=mock_assoc)

    servico_repo = AsyncMock()
    servico_repo.get_active_by_id = AsyncMock(return_value=mock_servico)

    svc = BuscaService()
    result = await svc._fase1_associacao(
        cliente_id=uuid.uuid4(),
        texto_normalizado="escavação manual de valas",
        assoc_repo=assoc_repo,
        servico_repo=servico_repo,
    )

    assert result is not None
    assert len(result) == 1
    assert result[0].score == 1.0
    assert result[0].origem_match == "ASSOCIACAO_DIRETA"


@pytest.mark.asyncio
async def test_fase1_returns_none_when_no_association():
    from app.services.busca_service import BuscaService

    assoc_repo = AsyncMock()
    assoc_repo.find_by_cliente_and_text = AsyncMock(return_value=None)

    svc = BuscaService()
    result = await svc._fase1_associacao(
        cliente_id=uuid.uuid4(),
        texto_normalizado="texto sem associacao",
        assoc_repo=assoc_repo,
        servico_repo=AsyncMock(),
    )

    assert result is None
