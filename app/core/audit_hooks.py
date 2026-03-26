"""
SQLAlchemy event listeners for automatic audit logging.

Monitored fields:
  - servico_tcpo.custo_unitario  (price change)
  - servico_tcpo.status_homologacao  (approval workflow)

Hooks are registered at import time.
Call register_audit_hooks() once in app startup (main.py lifespan).
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import event
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.enums import TipoOperacaoAuditoria

logger = get_logger(__name__)

# Fields to watch per model (table_name → list of column names)
_WATCHED_FIELDS: dict[str, list[str]] = {
    "servico_tcpo": ["custo_unitario", "status_homologacao"],
}


def _serialize(value) -> str | float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    return str(value)


def _after_flush_handler(session: Session, flush_context) -> None:
    """Intercepts dirty objects and writes audit records for watched fields."""
    from app.models.auditoria_log import AuditoriaLog

    entries: list[AuditoriaLog] = []

    for obj in session.dirty:
        table = getattr(obj.__class__, "__tablename__", None)
        if table not in _WATCHED_FIELDS:
            continue

        watched = _WATCHED_FIELDS[table]
        history_items = []

        for field in watched:
            attr = getattr(type(obj), field).impl
            hist = attr.get_history(obj, session.identity_map._modified)
            # SQLAlchemy history: (added, unchanged, deleted)
            if hist.deleted and hist.added:
                old_val = hist.deleted[0]
                new_val = hist.added[0]
                if old_val != new_val:
                    history_items.append((field, old_val, new_val))

        for field, old_val, new_val in history_items:
            entry = AuditoriaLog(
                tabela=table,
                registro_id=str(obj.id),
                operacao=TipoOperacaoAuditoria.UPDATE,
                campo_alterado=field,
                dados_anteriores={field: _serialize(old_val)},
                dados_novos={field: _serialize(new_val)},
            )
            entries.append(entry)
            logger.info(
                "audit_update",
                table=table,
                record_id=str(obj.id),
                field=field,
                old=_serialize(old_val),
                new=_serialize(new_val),
            )

    for entry in entries:
        session.add(entry)


def register_audit_hooks() -> None:
    """Register event listeners. Called once at application startup."""
    event.listen(Session, "after_flush", _after_flush_handler)
    logger.info("audit_hooks_registered")
