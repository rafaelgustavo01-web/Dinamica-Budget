import uuid
from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ComposicaoTcpo(Base):
    __tablename__ = "composicao_tcpo"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    servico_pai_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("servico_tcpo.id"),
        nullable=False,
        index=True,
    )
    insumo_filho_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("servico_tcpo.id"),
        nullable=False,
        index=True,
    )
    quantidade_consumo: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)

    servico_pai: Mapped["ServicoTcpo"] = relationship(
        back_populates="composicoes_pai",
        foreign_keys=[servico_pai_id],
        lazy="noload",
    )
    insumo_filho: Mapped["ServicoTcpo"] = relationship(
        back_populates="composicoes_filho",
        foreign_keys=[insumo_filho_id],
        lazy="noload",
    )
