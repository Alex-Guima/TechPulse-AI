"""Normalizador para itens brutos vindos de `RSSCollector` (ex: TechCrunch)."""
from __future__ import annotations

from typing import Any, Dict, List

from app.models.article import Article
from app.utils.dates import parse_date
from app.utils.text import clean_text


def normalize_rss_entries(raw_entries: List[Dict[str, Any]]) -> List[Article]:
    """Converte entradas brutas de um feed RSS em uma lista de `Article`.

    Args:
        raw_entries: Lista de dicts retornados por `RSSCollector.collect`.

    Returns:
        Lista de `Article` já validados e padronizados.
    """
    articles: List[Article] = []
    for entry in raw_entries:
        articles.append(
            Article(
                external_id=entry.get("id"),
                title=clean_text(entry.get("title")) or "Sem título",
                url=entry.get("link") or "",
                author=clean_text(entry.get("author")),
                published_at=parse_date(entry.get("published")),
                source=entry.get("source", "RSS"),
                summary=clean_text(entry.get("summary")),
                content=clean_text(entry.get("content")),
                tags=entry.get("tags") or [],
            )
        )
    return articles
