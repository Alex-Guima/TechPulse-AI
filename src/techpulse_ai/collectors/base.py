"""Contrato base que todo coletor de notícias deve implementar.

Um coletor tem uma única responsabilidade: buscar dados brutos em uma
fonte externa (feed RSS, API, etc.) e devolvê-los sem qualquer
transformação, limpeza ou classificação. Essas etapas ficam a cargo dos
normalizadores (`app.normalizers`).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseCollector(ABC):
    """Interface comum a todos os coletores de notícias.

    Subclasses devem implementar apenas `collect`, retornando uma lista
    de dados brutos (dicts, objetos do feedparser, etc.) exatamente como
    vieram da fonte. Nenhuma lógica de negócio deve existir aqui.
    """

    @abstractmethod
    def collect(self) -> list[Any]:
        """Busca e retorna os dados brutos da fonte.

        Returns:
            Lista de itens brutos, no formato nativo da fonte de origem.
        """
        raise NotImplementedError
