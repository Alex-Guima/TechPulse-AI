"""Normalizador para itens brutos vindos de `DevToCollector`."""
from __future__ import annotations

from typing import Any

from techpulse_ai.models.article import Article
from techpulse_ai.utils.dates import parse_date
from techpulse_ai.utils.text import clean_text


def normalize_devto_entries(raw_items: list[dict[str, Any]]) -> list[Article]:
    """Converte artigos brutos da API do Dev.to em uma lista de `Article`.

    Args:
        raw_items: Lista de dicts retornados por `DevToCollector.collect`.

    Returns:
        Lista de `Article` já validados e padronizados.
    """
    articles: list[Article] = []
    for item in raw_items:
        user = item.get("user") or {}
        articles.append(
            Article(
                id=str(item.get("id")) if item.get("id") is not None else None,
                title=clean_text(item.get("title")) or "Sem título",
                url=item.get("url") or "",
                author=user.get("name"),
                published_at=parse_date(item.get("published_at")),
                source="Dev.to",
                summary=clean_text(item.get("description")),
                content=None,
                tags=item.get("tag_list") or [],
            )
        )
    return articles
