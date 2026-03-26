import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class HistoricoBuscaCliente(Base):
    __tablename__ = "historico_busca_cliente"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cliente_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False, index=True
    )
    usuario_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True
    )
    texto_busca: Mapped[str] = mapped_column(Text, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    cliente: Mapped["Cliente"] = relationship(back_populates="historicos", lazy="noload")
    usuario: Mapped["Usuario"] = relationship(back_populates="historicos", lazy="noload")
