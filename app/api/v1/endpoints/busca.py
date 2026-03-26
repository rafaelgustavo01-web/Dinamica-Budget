from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db
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
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> BuscaServicoResponse:
    return await busca_service.buscar(
        request=request,
        usuario_email=current_user.email,
        db=db,
        background_tasks=background_tasks,
    )


@router.post("/associar", response_model=AssociacaoResponse, status_code=201)
async def criar_associacao(
    request: CriarAssociacaoRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AssociacaoResponse:
    return await busca_service.criar_associacao(
        request=request,
        usuario_email=current_user.email,
        db=db,
    )
