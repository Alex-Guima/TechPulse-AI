"""Coletor do Hacker News, usando a API pública oficial (Firebase).

Busca os IDs das top stories e, em seguida, os detalhes de cada uma.
Nenhuma transformação é feita aqui: os dicts retornados pela API são
devolvidos como estão para o normalizador correspondente.
"""
from __future__ import annotations

from typing import Any, Dict, List

import requests

from app.collectors.base import BaseCollector

TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
ITEM_URL_TEMPLATE = "https://hacker-news.firebaseio.com/v0/item/{item_id}.json"


class HackerNewsCollector(BaseCollector):
    """Coleta as principais histórias do Hacker News.

    Args:
        limit: Quantidade máxima de histórias a coletar.
        timeout: Timeout (em segundos) para as requisições HTTP.
    """

    def __init__(self, limit: int = 20, timeout: int = 10) -> None:
        self.limit = limit
        self.timeout = timeout

    def collect(self) -> List[Dict[str, Any]]:
        """Busca os IDs das top stories e retorna seus dados brutos.

        Returns:
            Lista de dicts, cada um representando um item retornado
            pela API do Hacker News (formato original, sem alterações).
        """
        response = requests.get(TOP_STORIES_URL, timeout=self.timeout)
        response.raise_for_status()
        story_ids = response.json()[: self.limit]

        raw_items: List[Dict[str, Any]] = []
        for story_id in story_ids:
            item_response = requests.get(
                ITEM_URL_TEMPLATE.format(item_id=story_id), timeout=self.timeout
            )
            item_response.raise_for_status()
            item_data = item_response.json()
            if item_data:
                raw_items.append(item_data)
        return raw_items
