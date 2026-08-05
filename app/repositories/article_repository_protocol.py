"""Abstração do repositório de artigos (Dependency Inversion).

Define o contrato mínimo que o `NewsCollectorService` depende para
persistir artigos, sem se acoplar à implementação concreta baseada em
SQLAlchemy/PostgreSQL (`app.repositories.article_repository.ArticleRepository`).

Este módulo também concentra os tipos que fazem parte desse contrato
(`SaveManyResult`, `ArticleSaveFailure`): eles descrevem o resultado que
qualquer implementação do protocolo deve produzir, então pertencem à
abstração, não a um detalhe da implementação concreta.

Não é necessário herdar explicitamente de `ArticleRepositoryProtocol`
para satisfazê-lo: `typing.Protocol` verifica conformidade pela forma
(duck typing estático), não por hierarquia de classes. É por isso que
`ArticleRepository` não declara herança deste `Protocol` — ele apenas
implementa os mesmos métodos, com as mesmas assinaturas.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Protocol, runtime_checkable

from app.models.article import Article


@dataclass
class ArticleSaveFailure:
    """Registra a falha ao tentar persistir um artigo específico.

    Attributes:
        url: URL do artigo que falhou — identidade natural do artigo
            antes de ele ser persistido (e ganhar um `id` de banco).
        reason: Descrição legível da causa da falha.
    """

    url: str
    reason: str


@dataclass
class SaveManyResult:
    """Resultado agregado de uma operação `save_many`.

    Attributes:
        saved: Quantidade de artigos novos, persistidos com sucesso.
        duplicates: Quantidade de artigos ignorados por já existirem
            (mesma URL).
        failed: Quantidade de artigos que falharam ao ser persistidos,
            por um motivo diferente de duplicidade.
        failures: Detalhe de cada falha (ver `ArticleSaveFailure`). Uma
            falha em um artigo nunca impede a tentativa dos demais.
    """

    saved: int = 0
    duplicates: int = 0
    failed: int = 0
    failures: List[ArticleSaveFailure] = field(default_factory=list)


@runtime_checkable
class ArticleRepositoryProtocol(Protocol):
    """Contrato mínimo que o `NewsCollectorService` espera de um repositório.

    Deliberadamente estreito (Interface Segregation): o serviço só
    precisa persistir artigos e saber quantos existem ao final — não
    precisa de `find_all`, `find_by_source`, `delete`, etc., então esses
    métodos (existentes em `ArticleRepository`) não fazem parte deste
    contrato.
    """

    def save_many(self, articles: List[Article]) -> SaveManyResult:
        """Persiste vários artigos, isolando duplicidade e falha por item."""
        ...

    def count(self) -> int:
        """Retorna o total de artigos persistidos."""
        ...
