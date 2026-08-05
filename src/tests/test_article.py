"""Testes unitários do modelo `Article`."""
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from techpulse_ai.models.article import Article


def test_article_creation_with_all_fields():
    article = Article(
        id="1",
        title="Título de teste",
        url="https://example.com/noticia",
        author="Autor Teste",
        published_at=datetime(2024, 1, 1, tzinfo=UTC),
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
    assert article.author is None
    assert article.published_at is None
    assert article.summary is None
    assert article.content is None
    assert article.tags == []


def test_article_requires_title_url_and_source():
    with pytest.raises(ValidationError):
        Article(url="https://example.com")
