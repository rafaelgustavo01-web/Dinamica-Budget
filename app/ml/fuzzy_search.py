"""
Fuzzy search module.

Primary strategy: pg_trgm via PostgreSQL (multi-worker safe, single source of truth).
The in-memory fallback with rapidfuzz is kept as a reserve strategy,
activatable via feature flag if DB CPU becomes a bottleneck.

pg_trgm threshold note:
  - pg_trgm similarity() returns 0.0-1.0
  - Default threshold in settings: 0.85
  - This is DIFFERENT from the semantic threshold (0.65)
"""

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def search_in_memory(
    query: str,
    catalog: list[tuple],
    threshold: float | None = None,
    limit: int = 10,
) -> list[tuple]:
    """
    Fallback in-memory fuzzy search using rapidfuzz token_set_ratio.
    catalog: list of (id, descricao) tuples.
    Returns list of (id, descricao, score) sorted by score desc.

    NOTE: Use only when pg_trgm is not available or DB is bottlenecked.
    """
    from rapidfuzz import fuzz, process

    t = threshold or settings.FUZZY_THRESHOLD
    choices = {str(item[0]): item[1] for item in catalog}

    results = process.extract(
        query,
        choices,
        scorer=fuzz.token_set_ratio,
        limit=limit,
        score_cutoff=t * 100,  # rapidfuzz uses 0-100 scale
    )

    return [
        (key, desc, score / 100.0)
        for desc, score, key in results
    ]
