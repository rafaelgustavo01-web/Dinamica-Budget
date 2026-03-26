from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db
from app.schemas.common import PaginatedResponse
from app.schemas.servico import (
    ExplodeComposicaoResponse,
    ServicoCreate,
    ServicoListParams,
    ServicoTcpoResponse,
)
from app.services.servico_catalog_service import servico_catalog_service

router = APIRouter(prefix="/servicos", tags=["servicos"])


@router.get("/", response_model=PaginatedResponse[ServicoTcpoResponse])
async def list_servicos(
    q: str | None = Query(default=None),
    categoria_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ServicoTcpoResponse]:
    params = ServicoListParams(q=q, categoria_id=categoria_id, page=page, page_size=page_size)
    return await servico_catalog_service.list_servicos(params, db)


@router.get("/{servico_id}", response_model=ServicoTcpoResponse)
async def get_servico(
    servico_id: UUID,
    _=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ServicoTcpoResponse:
    return await servico_catalog_service.get_servico(servico_id, db)


@router.get("/{servico_id}/composicao", response_model=ExplodeComposicaoResponse)
async def explode_composicao(
    servico_id: UUID,
    _=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ExplodeComposicaoResponse:
    return await servico_catalog_service.explode_composicao(servico_id, db)


@router.post("/", response_model=ServicoTcpoResponse, status_code=201)
async def create_servico(
    data: ServicoCreate,
    _=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ServicoTcpoResponse:
    return await servico_catalog_service.create_servico(data, db)
