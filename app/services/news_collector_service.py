"""Serviço responsável por orquestrar a coleta de notícias de todas as fontes.

O `NewsCollectorService` não conhece detalhes internos de nenhum
coletor ou normalizador específico: ele apenas recebe uma lista de
`NewsSource` (par coletor + normalizador) e executa cada um de forma
uniforme. Isso permite adicionar novas fontes sem alterar este arquivo,
e também torna o serviço facilmente testável com fontes falsas
(fakes/mocks), sem depender de rede.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List

from app.collectors.base import BaseCollector
from app.models.article import Article

NormalizerFunc = Callable[[List[Any]], List[Article]]


@dataclass(frozen=True)
class NewsSource:
    """Agrupa um coletor e seu respectivo normalizador.

    Attributes:
        name: Nome legível da fonte, usado em mensagens de log/erro.
        collector: Instância de um `BaseCollector` responsável por
            buscar os dados brutos.
        normalizer: Função que converte os dados brutos em `Article`.
    """

    name: str
    collector: BaseCollector
    normalizer: NormalizerFunc


class NewsCollectorService:
    """Executa todos os coletores configurados e consolida os artigos.

    Args:
        sources: Lista de `NewsSource` a serem executadas.
    """

    def __init__(self, sources: List[NewsSource]) -> None:
        self.sources = sources

    def collect_all(self) -> List[Article]:
        """Executa cada fonte configurada e retorna a lista consolidada.

        Uma falha em uma fonte específica (ex: indisponibilidade de
        rede) não interrompe a coleta das demais; o erro é registrado
        e a execução continua.

        Returns:
            Lista única de `Article`, reunindo o resultado de todas as
            fontes que executaram com sucesso.
        """
        all_articles: List[Article] = []

        for source in self.sources:
            try:
                raw_data = source.collector.collect()
                normalized_articles = source.normalizer(raw_data)
                all_articles.extend(normalized_articles)
            except Exception as error:  # noqa: BLE001 - isolamento intencional por fonte
                print(f"[NewsCollectorService] Falha ao coletar '{source.name}': {error}")

        return all_articles
