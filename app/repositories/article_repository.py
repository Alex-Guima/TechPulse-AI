"""Repositório de artigos — único ponto de acesso da aplicação ao PostgreSQL.

Nenhuma outra camada (em especial o `NewsCollectorService`) deve
executar SQL ou conhecer o SQLAlchemy diretamente: tudo passa por aqui.
Este módulo também é responsável por converter entre o modelo de
domínio (`Article`, Pydantic) e o modelo de persistência (`ArticleModel`,
SQLAlchemy ORM) — **nenhum tipo do SQLAlchemy sai desta classe**: todo
método público recebe e retorna exclusivamente objetos de domínio
(`Article`) ou tipos neutros (`bool`, `int`, `SaveManyResult`).

`ArticleRepository` implementa estruturalmente `ArticleRepositoryProtocol`
(ver `article_repository_protocol.py`) — não há herança explícita, já
que `Protocol` verifica conformidade pela forma dos métodos, não por
hierarquia de classes.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.database.exceptions import ArticleInsertError, DatabaseError
from app.database.models import ArticleModel
from app.database.session import session_scope
from app.models.article import Article
from app.repositories.article_repository_protocol import (
    ArticleRepositoryProtocol,
    ArticleSaveFailure,
    SaveManyResult,
)

# Re-exportados aqui para preservar compatibilidade com código/testes que
# já importam esses nomes diretamente deste módulo. A definição "oficial"
# vive em `article_repository_protocol.py`, junto do contrato ao qual
# pertencem.
__all__ = [
    "ArticleRepository",
    "ArticleRepositoryProtocol",
    "ArticleSaveFailure",
    "SaveManyResult",
]


class ArticleRepository:
    """Repositório responsável por toda a persistência de `Article`.

    Args:
        session_factory: Fábrica de sessões a ser usada. Se omitida,
            usa a fábrica padrão da aplicação. Permite injetar uma
            fábrica apontando para um banco de teste.
    """

    def __init__(self, session_factory: Optional[sessionmaker] = None) -> None:
        self._session_factory = session_factory

    def _session(self):
        """Abre uma sessão transacional configurada para este repositório.

        Pequeno atalho interno para não repetir
        `session_scope(self._session_factory)` em cada método público.
        """
        return session_scope(self._session_factory)

    def exists(self, url: str) -> bool:
        """Verifica se já existe um artigo persistido com a URL informada.

        Args:
            url: URL da notícia a verificar.

        Returns:
            `True` se já existir um registro com essa URL, `False` caso contrário.
        """
        with self._session() as session:
            statement = select(ArticleModel.id).where(ArticleModel.url == url)
            return session.execute(statement).first() is not None

    def save(self, article: Article) -> Optional[Article]:
        """Persiste um único artigo de forma idempotente por URL.

        Usa `INSERT ... ON CONFLICT (url) DO NOTHING`: se já existir um
        artigo com a mesma URL, nada é inserido e o método retorna
        `None` — sem precisar de uma checagem prévia (`exists`) nem de
        depender de capturar `IntegrityError` para detectar duplicidade.

        Args:
            article: Artigo (modelo de domínio) a ser persistido.

        Returns:
            O `Article` (modelo de domínio) persistido, já com o `id`
            atribuído pelo banco, ou `None` se a URL já existia.

        Raises:
            ArticleInsertError: para falhas de inserção que não sejam a
                duplicidade de URL (ex: dado inválido para uma coluna).
            DatabaseConnectionError, DatabaseTimeoutError: podem se
                propagar de `session_scope` para falhas de
                infraestrutura (conexão, timeout). `save_many` trata
                todas essas causas de forma uniforme através da
                classe-base comum, `DatabaseError`.
        """
        try:
            with self._session() as session:
                statement = (
                    pg_insert(ArticleModel)
                    .values(**self._to_insert_values(article))
                    .on_conflict_do_nothing(index_elements=["url"])
                    .returning(ArticleModel)
                )
                row = session.execute(statement).scalar_one_or_none()
                if row is None:
                    return None
                return self._to_domain(row)
        except SQLAlchemyError as error:
            raise ArticleInsertError(
                f"Falha ao inserir o artigo '{article.url}': {error}"
            ) from error

    def save_many(self, articles: List[Article]) -> SaveManyResult:
        """Persiste vários artigos, isolando falhas artigo a artigo.

        Cada artigo é salvo individualmente (via `save`). Uma falha em
        um artigo específico — de qualquer natureza coberta por
        `DatabaseError` (dado inválido, falha de conexão, timeout) —
        não interrompe os demais: ela é registrada em
        `SaveManyResult.failures` e a persistência continua
        normalmente para o restante da lista.

        Args:
            articles: Lista de artigos a persistir.

        Returns:
            `SaveManyResult` com a contagem de novos registros,
            duplicados ignorados, falhas e o detalhe de cada falha.
        """
        result = SaveManyResult()
        for article in articles:
            try:
                saved_article = self.save(article)
            except DatabaseError as error:
                result.failed += 1
                result.failures.append(ArticleSaveFailure(url=article.url, reason=str(error)))
                continue

            if saved_article is None:
                result.duplicates += 1
            else:
                result.saved += 1
        return result

    def find_all(self, limit: Optional[int] = None, offset: int = 0) -> List[Article]:
        """Retorna artigos persistidos, dos mais recentes para os mais antigos.

        Args:
            limit: Quantidade máxima de artigos a retornar (opcional).
            offset: Quantidade de registros a pular, para paginação.

        Returns:
            Lista de `Article` (modelo de domínio).
        """
        with self._session() as session:
            statement = (
                select(ArticleModel)
                .order_by(ArticleModel.published_at.desc().nullslast())
                .offset(offset)
            )
            statement = self._apply_limit(statement, limit)
            rows = session.execute(statement).scalars().all()
            return [self._to_domain(row) for row in rows]

    def find_latest(self, limit: int = 10) -> List[Article]:
        """Retorna os `limit` artigos mais recentes (por `published_at`).

        Args:
            limit: Quantidade de artigos a retornar.

        Returns:
            Lista de `Article` (modelo de domínio).
        """
        return self.find_all(limit=limit)

    def find_by_source(self, source: str, limit: Optional[int] = None) -> List[Article]:
        """Retorna artigos persistidos de uma fonte específica.

        Args:
            source: Nome da fonte (ex: "Dev.to", "Hacker News").
            limit: Quantidade máxima de artigos a retornar (opcional).

        Returns:
            Lista de `Article` (modelo de domínio) daquela fonte.
        """
        with self._session() as session:
            statement = (
                select(ArticleModel)
                .where(ArticleModel.source == source)
                .order_by(ArticleModel.published_at.desc().nullslast())
            )
            statement = self._apply_limit(statement, limit)
            rows = session.execute(statement).scalars().all()
            return [self._to_domain(row) for row in rows]

    def count(self) -> int:
        """Retorna o total de artigos persistidos no banco.

        Returns:
            Quantidade total de registros na tabela `articles`.
        """
        with self._session() as session:
            statement = select(func.count()).select_from(ArticleModel)
            return session.execute(statement).scalar_one()

    def delete(self, article_id: int) -> bool:
        """Remove um artigo pelo seu identificador (chave primária).

        Args:
            article_id: Identificador (`id`) do artigo a remover.

        Returns:
            `True` se o artigo existia e foi removido, `False` caso
            não tenha sido encontrado nenhum artigo com esse `id`.
        """
        with self._session() as session:
            orm_article = session.get(ArticleModel, article_id)
            if orm_article is None:
                return False
            session.delete(orm_article)
            return True

    @staticmethod
    def _apply_limit(statement: Select, limit: Optional[int]) -> Select:
        """Aplica `.limit(...)` a uma query apenas quando um limite é informado.

        Extraído para evitar repetir esse `if` em `find_all` e
        `find_by_source`.
        """
        return statement if limit is None else statement.limit(limit)

    @staticmethod
    def _to_insert_values(article: Article) -> dict:
        """Converte o domínio para os valores usados na instrução INSERT.

        `id`, `created_at` e `updated_at` ficam de fora de propósito:
        são sempre atribuídos pelo banco (chave primária autoincremento
        e `server_default=func.now()`, respectivamente).
        """
        return {
            "title": article.title,
            "url": article.url,
            "author": article.author,
            "published_at": article.published_at,
            "source": article.source,
            "summary": article.summary,
            "content": article.content,
            "tags": list(article.tags),
            "external_id": article.external_id,
        }

    @staticmethod
    def _to_domain(orm_article: ArticleModel) -> Article:
        """Converte o modelo ORM para o modelo de domínio (`Article`).

        `id` é sempre a chave primária do banco; o identificador
        original da fonte (quando existir) vem de `external_id` — nunca
        os dois significados são misturados em um único campo.
        """
        return Article(
            id=str(orm_article.id),
            external_id=orm_article.external_id,
            title=orm_article.title,
            url=orm_article.url,
            author=orm_article.author,
            published_at=orm_article.published_at,
            source=orm_article.source,
            summary=orm_article.summary,
            content=orm_article.content,
            tags=list(orm_article.tags or []),
        )
