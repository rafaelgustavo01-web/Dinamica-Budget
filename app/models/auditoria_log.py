"""
Audit log table — records all write operations on sensitive fields.
Populated via SQLAlchemy event listeners (hooks), not manually.

Captures:
  - Price changes on servico_tcpo.custo_unitario
  - Status changes on servico_tcpo.status_homologacao
  - Any explicit CREATE/DELETE on servico_tcpo
"""

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum as SAEnum, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import TipoOperacaoAuditoria


class AuditoriaLog(Base):
    __tablename__ = "auditoria_log"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tabela: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    registro_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True  # UUID as string for flexibility
    )
    operacao: Mapped[TipoOperacaoAuditoria] = mapped_column(
        SAEnum(TipoOperacaoAuditoria, name="tipo_operacao_auditoria_enum"),
        nullable=False,
    )
    campo_alterado: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dados_anteriores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    dados_novos: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    usuario_origem: Mapped[str | None] = mapped_column(String(255), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
