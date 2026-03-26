from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_cliente_access
from app.schemas.busca import (
    AssociacaoResponse,
    BuscaServicoRequest,
    BuscaServicoResponse,
    CriarAssociacaoRequest,
)
from app.services.busca_service import busca_service

router = APIRouter(prefix="/busca", tags=["busca"])


@router.post("/servicos", response_model=BuscaServicoResponse)
async def buscar_servicos(
    request: BuscaServicoRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> BuscaServicoResponse:
    await require_cliente_access(request.cliente_id, current_user, db)
    return await busca_service.buscar(
        request=request,
        usuario_id=current_user.id,
        db=db,
    )


@router.post("/associar", response_model=AssociacaoResponse, status_code=201)
async def criar_associacao(
    request: CriarAssociacaoRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AssociacaoResponse:
    await require_cliente_access(request.cliente_id, current_user, db)
    return await busca_service.criar_associacao(
        request=request,
        usuario_id=current_user.id,
        db=db,
    )
