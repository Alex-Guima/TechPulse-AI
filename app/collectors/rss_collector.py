"""Coletor genérico para qualquer fonte baseada em feed RSS/Atom.

Reutilizado diretamente para o TechCrunch e usado como classe-base para
o GitHub Blog (ver `github_collector.py`), evitando duplicar a lógica de
leitura de feeds.
"""
from __future__ import annotations

from typing import Any, Dict, List

import feedparser

from app.collectors.base import BaseCollector


class RSSCollector(BaseCollector):
    """Coleta itens brutos de um feed RSS/Atom.

    Args:
        feed_url: URL do feed RSS/Atom a ser lido.
        source_name: Nome legível da fonte (usado depois pelo normalizador).
    """

    def __init__(self, feed_url: str, source_name: str) -> None:
        self.feed_url = feed_url
        self.source_name = source_name

    def collect(self) -> List[Dict[str, Any]]:
        """Faz o parse do feed e retorna as entradas brutas.

        Cada entrada é um dict simples contendo os campos originais do
        feedparser mais o nome da fonte, para uso posterior pelo
        normalizador.

        Returns:
            Lista de dicionários com os dados brutos de cada entrada.
        """
        parsed_feed = feedparser.parse(self.feed_url)

        raw_entries: List[Dict[str, Any]] = []
        for entry in parsed_feed.entries:
            raw_entries.append(
                {
                    "source": self.source_name,
                    "title": entry.get("title"),
                    "link": entry.get("link"),
                    "author": entry.get("author"),
                    "published": entry.get("published") or entry.get("updated"),
                    "summary": entry.get("summary"),
                    "content": (
                        entry.get("content")[0].get("value")
                        if entry.get("content")
                        else None
                    ),
                    "tags": [tag.get("term") for tag in entry.get("tags", []) if tag.get("term")],
                    "id": entry.get("id") or entry.get("link"),
                }
            )
        return raw_entries
