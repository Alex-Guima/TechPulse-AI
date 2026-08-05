"""Fixtures compartilhadas para os testes de persistência da Fase 2.

Os testes de `ArticleRepository` (em `test_article_repository.py`)
precisam de um PostgreSQL de teste real (não usamos SQLite, conforme
definido para o projeto). Se não houver um banco de teste acessível,
esses testes são pulados automaticamente (`pytest.skip`), para não
quebrar a suíte em ambientes sem PostgreSQL configurado (ex: CI sem
serviço de banco, ou execução local rápida).

Recomenda-se apontar para um banco *dedicado a testes*, diferente do
banco de desenvolvimento — por padrão, usamos o mesmo nome do banco
configurado em `.env` com o sufixo `_test`.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from app.config.settings import get_settings
from app.database.base import Base


def _build_test_database_url() -> str:
    settings = get_settings()
    test_database_name = f"{settings.database_name}_test"
    return (
        f"postgresql+psycopg2://{settings.database_user}:{settings.database_password}"
        f"@{settings.database_host}:{settings.database_port}/{test_database_name}"
    )


@pytest.fixture(scope="session")
def test_engine():
    """Engine apontando para um banco de PostgreSQL dedicado a testes.

    Cria as tabelas no início da sessão de testes e as remove ao final.
    Usar `create_all`/`drop_all` aqui é aceitável porque é um banco
    efêmero de testes — a fonte de verdade do schema em desenvolvimento
    e produção continua sendo o Alembic (ver `alembic/versions/`).
    """
    engine = create_engine(_build_test_database_url())

    try:
        with engine.connect():
            pass
    except OperationalError as error:
        pytest.skip(
            "PostgreSQL de teste indisponível "
            f"({error.__class__.__name__}); pulando testes de persistência. "
            "Configure um banco de teste (ex: 'techpulse_test') para executá-los."
        )

    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def session_factory(test_engine):
    """Session factory de teste, vinculada ao `test_engine`."""
    return sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def repository(session_factory):
    """`ArticleRepository` configurado para usar o banco de teste."""
    from app.repositories.article_repository import ArticleRepository

    return ArticleRepository(session_factory=session_factory)


@pytest.fixture(autouse=True)
def _clean_articles_table(test_engine):
    """Limpa a tabela `articles` após cada teste, mantendo os testes isolados."""
    yield
    with test_engine.begin() as connection:
        connection.execute(Base.metadata.tables["articles"].delete())
