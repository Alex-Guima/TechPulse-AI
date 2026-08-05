"""Testes unitários do modelo `Article`."""
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.article import Article


def test_article_creation_with_all_fields():
    article = Article(
        id="1",
        title="Título de teste",
        url="https://example.com/noticia",
        author="Autor Teste",
        published_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        source="TechCrunch",
        summary="Resumo curto",
        content="Conteúdo completo",
        tags=["ia", "python"],
    )

    assert article.id == "1"
    assert article.title == "Título de teste"
    assert article.tags == ["ia", "python"]


def test_article_creation_with_minimal_fields_defaults_to_none():
    article = Article(title="Só título", url="https://example.com", source="Dev.to")

    assert article.id is None
    assert article.external_id is None
    assert article.author is None
    assert article.published_at is None
    assert article.summary is None
    assert article.content is None
    assert article.tags == []


def test_article_external_id_is_independent_from_id():
    """`id` (chave do banco) e `external_id` (identificador da fonte)
    não devem ser confundidos: um normalizador preenche `external_id` e
    deixa `id` em branco; o repositório é quem preenche `id`."""
    article = Article(
        title="Notícia do Hacker News",
        url="https://news.ycombinator.com/item?id=123",
        source="Hacker News",
        external_id="123",
    )

    assert article.id is None
    assert article.external_id == "123"


def test_article_requires_title_url_and_source():
    with pytest.raises(ValidationError):
        Article(url="https://example.com")
