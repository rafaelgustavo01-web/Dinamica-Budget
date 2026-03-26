from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ServicoTcpoResponse(BaseModel):
    id: UUID
    codigo_origem: str
    descricao: str
    unidade_medida: str
    custo_unitario: Decimal
    categoria_id: int | None

    model_config = ConfigDict(from_attributes=True)


class ComposicaoItemResponse(BaseModel):
    id: UUID
    insumo_filho_id: UUID
    descricao_filho: str
    unidade_medida: str
    quantidade_consumo: Decimal
    custo_unitario: Decimal
    custo_total: Decimal  # quantidade_consumo * custo_unitario

    model_config = ConfigDict(from_attributes=True)


class ExplodeComposicaoResponse(BaseModel):
    servico: ServicoTcpoResponse
    itens: list[ComposicaoItemResponse]
    custo_total_composicao: Decimal


class ServicoListParams(BaseModel):
    q: str | None = None
    categoria_id: int | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ServicoCreate(BaseModel):
    codigo_origem: str
    descricao: str
    unidade_medida: str
    custo_unitario: Decimal
    categoria_id: int | None = None
