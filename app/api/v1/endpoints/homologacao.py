from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db
from app.models.usuario import UsuarioPerfil
from app.schemas.common import PaginatedResponse
from app.schemas.homologacao import (
    AprovarHomologacaoRequest,
    AprovarHomologacaoResponse,
    CriarItemProprioRequest,
    ItemPendenteResponse,
)
from app.schemas.servico import ServicoTcpoResponse
from app.services.homologacao_service import homologacao_service

router = APIRouter(prefix="/homologacao", tags=["homologacao"])


async def _get_perfis(current_user, db: AsyncSession) -> list[str]:
    """Extract the current user's perfis from the RBAC table."""
    from sqlalchemy import select

    result = await db.execute(
        select(UsuarioPerfil.perfil).where(UsuarioPerfil.usuario_id == current_user.id)
    )
    perfis = [row[0] for row in result.fetchall()]
    if current_user.is_admin:
        perfis.append("ADMIN")
    return perfis


@router.get("/pendentes", response_model=PaginatedResponse[ItemPendenteResponse])
async def listar_pendentes(
    cliente_id: UUID = Query(...),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ItemPendenteResponse]:
    return await homologacao_service.listar_pendentes(
        cliente_id=cliente_id,
        page=page,
        page_size=page_size,
        db=db,
    )


@router.post("/aprovar", response_model=AprovarHomologacaoResponse)
async def aprovar_item(
    request: AprovarHomologacaoRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AprovarHomologacaoResponse:
    perfis = await _get_perfis(current_user, db)
    return await homologacao_service.aprovar(
        request=request,
        aprovador_email=current_user.email,
        aprovador_id=current_user.id,
        aprovador_perfis=perfis,
        db=db,
    )


@router.post("/itens-proprios", response_model=ServicoTcpoResponse, status_code=201)
async def criar_item_proprio(
    request: CriarItemProprioRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ServicoTcpoResponse:
    servico = await homologacao_service.criar_item_proprio(request, db)
    return ServicoTcpoResponse.model_validate(servico)
