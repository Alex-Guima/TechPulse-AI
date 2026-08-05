"""Normalizador para itens brutos vindos de `HackerNewsCollector`."""
from __future__ import annotations

from typing import Any, Dict, List

from app.models.article import Article
from app.utils.dates import parse_date
from app.utils.text import clean_text


def normalize_hackernews_entries(raw_items: List[Dict[str, Any]]) -> List[Article]:
    """Converte itens brutos da API do Hacker News em uma lista de `Article`.

    Itens do tipo "job" ou sem título são ignorados, pois não representam
    notícias de tecnologia relevantes para o domínio do projeto.

    Args:
        raw_items: Lista de dicts retornados por `HackerNewsCollector.collect`.

    Returns:
        Lista de `Article` já validados e padronizados.
    """
    articles: List[Article] = []
    for item in raw_items:
        if not item or not item.get("title"):
            continue

        story_id = item.get("id")
        articles.append(
            Article(
                external_id=str(story_id) if story_id is not None else None,
                title=clean_text(item.get("title")) or "Sem título",
                url=item.get("url") or f"https://news.ycombinator.com/item?id={story_id}",
                author=item.get("by"),
                published_at=parse_date(item.get("time")),
                source="Hacker News",
                summary=None,
                content=clean_text(item.get("text")),
                tags=[item.get("type")] if item.get("type") else [],
            )
        )
    return articles
