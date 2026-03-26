import enum
import uuid
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class OrigemAssociacao(str, enum.Enum):
    MANUAL_USUARIO = "MANUAL_USUARIO"
    IA_CONSOLIDADA = "IA_CONSOLIDADA"


class AssociacaoTcpo(Base):
    __tablename__ = "associacao_tcpo"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cliente_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False, index=True
    )
    texto_busca_original: Mapped[str] = mapped_column(String(255), nullable=False)
    servico_tcpo_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("servico_tcpo.id"),
        nullable=False,
        index=True,
    )
    origem_associacao: Mapped[OrigemAssociacao] = mapped_column(
        SAEnum(OrigemAssociacao, name="origem_associacao_enum"), nullable=False
    )
    confiabilidade_score: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 2), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    cliente: Mapped["Cliente"] = relationship(back_populates="associacoes", lazy="noload")
    servico_tcpo: Mapped["ServicoTcpo"] = relationship(
        back_populates="associacoes", lazy="noload"
    )
