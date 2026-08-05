"""Serviço responsável por orquestrar a coleta de notícias de todas as fontes.

O `NewsCollectorService` não conhece detalhes internos de nenhum
coletor ou normalizador específico: ele apenas recebe uma lista de
`NewsSource` (par coletor + normalizador) e executa cada um de forma
uniforme. Isso permite adicionar novas fontes sem alterar este arquivo,
e também torna o serviço facilmente testável com fontes falsas
(fakes/mocks), sem depender de rede.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

from app.collectors.base import BaseCollector
from app.models.article import Article
from app.repositories.article_repository_protocol import ArticleRepositoryProtocol

# Import real (não apenas para type-checking): `article_repository_protocol`
# não depende de SQLAlchemy, só do modelo de domínio (`Article`). Isso
# preserva a garantia de que o serviço não conhece SQLAlchemy, e ainda
# torna o contrato do repositório verificável em vez de apenas descrito
# em comentário.
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


@dataclass
class CollectionStats:
    """Estatísticas de uma execução de coleta + persistência.

    Attributes:
        sources_checked: Quantidade de fontes configuradas/consultadas.
        articles_found: Total de artigos retornados pelos coletores
            (antes da deduplicação).
        new_records: Quantidade de artigos novos, efetivamente
            persistidos nesta execução.
        duplicates_ignored: Quantidade de artigos ignorados por já
            existirem no banco (mesma URL).
        failed_records: Quantidade de artigos que falharam ao ser
            persistidos (motivo diferente de duplicidade) — ver
            `SaveManyResult.failures` para o detalhe de cada falha.
        total_persisted: Total de artigos armazenados no banco (soma
            de todas as execuções, não apenas desta).
        execution_time_seconds: Tempo total gasto em `collect_and_persist`.
    """

    sources_checked: int = 0
    articles_found: int = 0
    new_records: int = 0
    duplicates_ignored: int = 0
    failed_records: int = 0
    total_persisted: int = 0
    execution_time_seconds: float = 0.0

    def as_report(self) -> str:
        """Formata as estatísticas como um relatório legível para o terminal."""
        separator = "=" * 25
        lines = [
            separator,
            "TechPulse AI",
            separator,
            f"Fontes consultadas: {self.sources_checked}",
            f"Artigos encontrados: {self.articles_found}",
            f"Novos registros: {self.new_records}",
            f"Duplicados ignorados: {self.duplicates_ignored}",
            f"Falhas ao persistir: {self.failed_records}",
            f"Total persistido: {self.total_persisted}",
            f"Tempo de execução: {self.execution_time_seconds:.2f}s",
        ]
        return "\n".join(lines)


@dataclass
class CollectionResult:
    """Agrupa os artigos coletados nesta execução e as estatísticas geradas.

    Attributes:
        articles: Artigos coletados e normalizados nesta execução
            (antes da deduplicação pelo repositório).
        stats: Estatísticas consolidadas da execução.
    """

    articles: List[Article] = field(default_factory=list)
    stats: CollectionStats = field(default_factory=CollectionStats)


class NewsCollectorService:
    """Executa todos os coletores configurados e consolida os artigos.

    Args:
        sources: Lista de `NewsSource` a serem executadas.
        repository: Repositório opcional usado para persistir os
            artigos coletados (ver `collect_and_persist`). O serviço
            não conhece SQLAlchemy: depende apenas do contrato formal
            `ArticleRepositoryProtocol` (`save_many` + `count`).
            Qualquer objeto compatível estruturalmente é aceito, sem
            necessidade de herança explícita.
    """

    def __init__(
        self,
        sources: List[NewsSource],
        repository: Optional[ArticleRepositoryProtocol] = None,
    ) -> None:
        self.sources = sources
        self.repository = repository

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

    def collect_and_persist(self) -> CollectionResult:
        """Coleta artigos de todas as fontes e persiste os novos no repositório.

        Reaproveita `collect_all()` para a etapa de coleta/normalização
        e delega toda a persistência ao `repository` configurado — o
        serviço nunca executa SQL diretamente.

        Returns:
            `CollectionResult` contendo os artigos coletados nesta
            execução e as estatísticas consolidadas (novos registros,
            duplicados, total persistido e tempo de execução).

        Raises:
            ValueError: se o serviço não tiver sido configurado com um
                `repository`.
        """
        if self.repository is None:
            raise ValueError(
                "NewsCollectorService precisa de um 'repository' configurado "
                "para chamar collect_and_persist()."
            )

        start_time = time.perf_counter()
        articles = self.collect_all()
        save_result = self.repository.save_many(articles)
        elapsed_seconds = time.perf_counter() - start_time

        stats = CollectionStats(
            sources_checked=len(self.sources),
            articles_found=len(articles),
            new_records=save_result.saved,
            duplicates_ignored=save_result.duplicates,
            failed_records=save_result.failed,
            total_persisted=self.repository.count(),
            execution_time_seconds=elapsed_seconds,
        )
        return CollectionResult(articles=articles, stats=stats)
