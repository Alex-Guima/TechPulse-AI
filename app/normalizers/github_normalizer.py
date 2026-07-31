"""Normalizador para itens brutos vindos de `GitHubBlogCollector`.

Como o `GitHubBlogCollector` herda de `RSSCollector` e produz dados no
mesmo formato, este normalizador reaproveita `normalize_rss_entries`.
Mantê-lo em um arquivo próprio permite evoluir a regra de normalização
do GitHub de forma independente, caso a fonte mude no futuro.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.models.article import Article
from app.normalizers.rss_normalizer import normalize_rss_entries


def normalize_github_entries(raw_entries: List[Dict[str, Any]]) -> List[Article]:
    """Converte entradas brutas do GitHub Blog em uma lista de `Article`.

    Args:
        raw_entries: Lista de dicts retornados por `GitHubBlogCollector.collect`.

    Returns:
        Lista de `Article` já validados e padronizados.
    """
    return normalize_rss_entries(raw_entries)
