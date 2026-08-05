"""Testes do `ArticleRepository`: persistência, duplicidade e consultas.

Requerem um PostgreSQL de teste acessível (ver `tests/conftest.py`);
caso contrário, são pulados automaticamente.
"""
from datetime import datetime, timezone

from app.models.article import Article
from app.repositories.article_repository import SaveManyResult


def _make_article(url: str, source: str = "TechCrunch", **overrides) -> Article:
    data = {
        "title": f"Artigo {url}",
        "url": url,
        "source": source,
    }
    data.update(overrides)
    return Article(**data)


def test_save_persists_a_new_article(repository):
    article = _make_article("https://example.com/artigo-1")

    saved = repository.save(article)

    assert saved is not None
    assert saved.url == "https://example.com/artigo-1"
    assert repository.count() == 1


def test_save_returns_none_for_duplicate_url(repository):
    article = _make_article("https://example.com/artigo-2")
    repository.save(article)

    duplicate_result = repository.save(article)

    assert duplicate_result is None
    assert repository.count() == 1


def test_exists_detects_persisted_url(repository):
    article = _make_article("https://example.com/artigo-3")
    repository.save(article)

    assert repository.exists("https://example.com/artigo-3") is True
    assert repository.exists("https://example.com/nao-existe") is False


def test_save_many_counts_new_and_duplicates(repository):
    article_1 = _make_article("https://example.com/artigo-4")
    article_2 = _make_article("https://example.com/artigo-5")
    repository.save(article_1)

    result: SaveManyResult = repository.save_many([article_1, article_2])

    assert result.saved == 1
    assert result.duplicates == 1
    assert repository.count() == 2


def test_find_by_source_filters_correctly(repository):
    repository.save(_make_article("https://example.com/artigo-6", source="Dev.to"))
    repository.save(_make_article("https://example.com/artigo-7", source="Hacker News"))

    devto_articles = repository.find_by_source("Dev.to")

    assert len(devto_articles) == 1
    assert devto_articles[0].source == "Dev.to"


def test_find_latest_orders_by_published_at_desc(repository):
    older = _make_article(
        "https://example.com/artigo-8",
        published_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    newer = _make_article(
        "https://example.com/artigo-9",
        published_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
    )
    repository.save(older)
    repository.save(newer)

    latest = repository.find_latest(limit=1)

    assert len(latest) == 1
    assert latest[0].url == "https://example.com/artigo-9"


def test_find_all_respects_limit_and_offset(repository):
    for index in range(3):
        repository.save(
            _make_article(
                f"https://example.com/artigo-page-{index}",
                published_at=datetime(2024, 1, index + 1, tzinfo=timezone.utc),
            )
        )

    first_page = repository.find_all(limit=2, offset=0)
    second_page = repository.find_all(limit=2, offset=2)

    assert len(first_page) == 2
    assert len(second_page) == 1


def test_delete_removes_article(repository):
    saved = repository.save(_make_article("https://example.com/artigo-10"))

    # `save()` retorna o modelo de domínio (`Article`), cujo `id` é uma
    # string (chave primária do banco, serializada); `delete()` recebe
    # a chave primária como `int`.
    deleted = repository.delete(int(saved.id))

    assert deleted is True
    assert repository.count() == 0


def test_delete_returns_false_for_unknown_id(repository):
    assert repository.delete(999_999) is False


def test_save_returns_domain_article_not_orm_model(repository):
    """`save()` nunca deve vazar o tipo ORM (`ArticleModel`) para fora
    do repositório — só o modelo de domínio (`Article`, Pydantic)."""
    saved = repository.save(_make_article("https://example.com/artigo-11"))

    assert isinstance(saved, Article)
    assert isinstance(saved.id, str)


def test_save_persists_external_id(repository):
    article = _make_article("https://example.com/artigo-12", external_id="hn-123")

    saved = repository.save(article)

    assert saved.external_id == "hn-123"

    fetched = repository.find_by_source("TechCrunch")
    matching = [item for item in fetched if item.url == "https://example.com/artigo-12"]
    assert len(matching) == 1
    assert matching[0].external_id == "hn-123"


def test_save_many_isolates_a_failing_article_and_persists_the_rest(repository):
    """Um artigo com dado inválido (título maior que a coluna suporta)
    não deve impedir a persistência dos demais artigos do lote."""
    good_article = _make_article("https://example.com/artigo-valido")
    invalid_article = _make_article(
        "https://example.com/artigo-invalido",
        title="x" * 600,  # excede o VARCHAR(500) da coluna `title`
    )

    result = repository.save_many([invalid_article, good_article])

    assert result.saved == 1
    assert result.failed == 1
    assert result.duplicates == 0
    assert len(result.failures) == 1
    assert result.failures[0].url == "https://example.com/artigo-invalido"
    assert repository.count() == 1
