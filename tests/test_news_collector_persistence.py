"""Testes de `NewsCollectorService.collect_and_persist` (Fase 2).

Usa um repositório falso, totalmente em memória, para validar a
orquestração entre coleta e persistência sem depender de PostgreSQL
nem de SQLAlchemy.
"""
from dataclasses import dataclass
from typing import List

import pytest

from app.collectors.base import BaseCollector
from app.models.article import Article
from app.services.news_collector_service import (
    CollectionResult,
    NewsCollectorService,
    NewsSource,
)


class FakeCollector(BaseCollector):
    """Coletor falso que retorna dados pré-definidos, sem rede."""

    def __init__(self, raw_data):
        self.raw_data = raw_data

    def collect(self):
        return self.raw_data


def fake_normalizer(raw_data):
    return [
        Article(title=item["title"], url=item["url"], source="Fake Source")
        for item in raw_data
    ]


@dataclass
class FakeSaveManyResult:
    saved: int
    duplicates: int
    failed: int = 0


class FakeRepository:
    """Repositório falso em memória, satisfazendo estruturalmente
    `ArticleRepositoryProtocol` (`save_many` + `count`) sem herdar dele —
    exatamente como o `ArticleRepository` real."""

    def __init__(self, existing_urls=None, failing_urls=None):
        self.stored_urls = set(existing_urls or [])
        self.failing_urls = set(failing_urls or [])
        self.save_many_calls: List[List[Article]] = []

    def save_many(self, articles: List[Article]) -> FakeSaveManyResult:
        self.save_many_calls.append(articles)
        saved = 0
        duplicates = 0
        failed = 0
        for article in articles:
            if article.url in self.failing_urls:
                failed += 1
            elif article.url in self.stored_urls:
                duplicates += 1
            else:
                self.stored_urls.add(article.url)
                saved += 1
        return FakeSaveManyResult(saved=saved, duplicates=duplicates, failed=failed)

    def count(self) -> int:
        return len(self.stored_urls)


def test_collect_and_persist_returns_articles_and_stats():
    source = NewsSource(
        name="Fonte A",
        collector=FakeCollector([{"title": "Notícia 1", "url": "https://a.com/1"}]),
        normalizer=fake_normalizer,
    )
    repository = FakeRepository()
    service = NewsCollectorService(sources=[source], repository=repository)

    result: CollectionResult = service.collect_and_persist()

    assert len(result.articles) == 1
    assert result.stats.sources_checked == 1
    assert result.stats.articles_found == 1
    assert result.stats.new_records == 1
    assert result.stats.duplicates_ignored == 0
    assert result.stats.failed_records == 0
    assert result.stats.total_persisted == 1
    assert result.stats.execution_time_seconds >= 0
    assert "TechPulse AI" in result.stats.as_report()


def test_collect_and_persist_counts_duplicates_already_stored():
    source = NewsSource(
        name="Fonte A",
        collector=FakeCollector([{"title": "Notícia 1", "url": "https://a.com/1"}]),
        normalizer=fake_normalizer,
    )
    repository = FakeRepository(existing_urls={"https://a.com/1"})
    service = NewsCollectorService(sources=[source], repository=repository)

    result = service.collect_and_persist()

    assert result.stats.new_records == 0
    assert result.stats.duplicates_ignored == 1
    assert result.stats.failed_records == 0
    assert result.stats.total_persisted == 1


def test_collect_and_persist_reflects_failed_records():
    source = NewsSource(
        name="Fonte A",
        collector=FakeCollector(
            [
                {"title": "Notícia 1", "url": "https://a.com/1"},
                {"title": "Notícia 2", "url": "https://a.com/2"},
            ]
        ),
        normalizer=fake_normalizer,
    )
    repository = FakeRepository(failing_urls={"https://a.com/1"})
    service = NewsCollectorService(sources=[source], repository=repository)

    result = service.collect_and_persist()

    assert result.stats.new_records == 1
    assert result.stats.duplicates_ignored == 0
    assert result.stats.failed_records == 1
    assert "Falhas ao persistir: 1" in result.stats.as_report()


def test_collect_and_persist_without_repository_raises_value_error():
    service = NewsCollectorService(sources=[])

    with pytest.raises(ValueError):
        service.collect_and_persist()


def test_collect_all_still_works_without_repository():
    """Garante que o comportamento da Fase 1 permanece intacto."""
    source = NewsSource(
        name="Fonte A",
        collector=FakeCollector([{"title": "Notícia 1", "url": "https://a.com/1"}]),
        normalizer=fake_normalizer,
    )
    service = NewsCollectorService(sources=[source])

    articles = service.collect_all()

    assert len(articles) == 1
