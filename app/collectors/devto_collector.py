"""Coletor do Dev.to, usando a API pública de artigos.

Apenas busca a lista de artigos e devolve o JSON bruto retornado pela
API, sem qualquer transformação.
"""
from __future__ import annotations

from typing import Any, Dict, List

import requests

from app.collectors.base import BaseCollector

DEVTO_ARTICLES_URL = "https://dev.to/api/articles"


class DevToCollector(BaseCollector):
    """Coleta artigos recentes do Dev.to.

    Args:
        tag: Tag opcional para filtrar os artigos (ex: "python").
        per_page: Quantidade de artigos a buscar por requisição.
        timeout: Timeout (em segundos) para a requisição HTTP.
    """

    def __init__(self, tag: str | None = None, per_page: int = 20, timeout: int = 10) -> None:
        self.tag = tag
        self.per_page = per_page
        self.timeout = timeout

    def collect(self) -> List[Dict[str, Any]]:
        """Busca artigos na API do Dev.to e retorna os dados brutos.

        Returns:
            Lista de dicts no formato original retornado pela API do Dev.to.
        """
        params: Dict[str, Any] = {"per_page": self.per_page}
        if self.tag:
            params["tag"] = self.tag

        response = requests.get(DEVTO_ARTICLES_URL, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
