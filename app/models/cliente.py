import uuid
from uuid import UUID

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from datetime import datetime


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome_fantasia: Mapped[str] = mapped_column(String(255), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(14), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    associacoes: Mapped[list["AssociacaoInteligente"]] = relationship(
        "AssociacaoInteligente", foreign_keys="AssociacaoInteligente.cliente_id",
        lazy="noload"
    )
    historicos: Mapped[list["HistoricoBuscaCliente"]] = relationship(
        back_populates="cliente", lazy="noload"
    )
