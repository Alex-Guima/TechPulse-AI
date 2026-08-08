"""Testes unitários do `NewsCollectorService`, usando fontes falsas (fakes).

Como o serviço só conhece a interface `BaseCollector` e uma função
normalizadora, é possível testá-lo sem qualquer chamada de rede.
"""
from techpulse_ai.collectors.base import BaseCollector
from techpulse_ai.models.article import Article
from techpulse_ai.services.news_collector_service import (
    NewsCollectorService,
    NewsSource,
)


class FakeCollector(BaseCollector):
    """Coletor falso que retorna dados pré-definidos, sem rede."""

    def __init__(self, raw_data):
        self.raw_data = raw_data

    def collect(self):
        return self.raw_data


class FailingCollector(BaseCollector):
    """Coletor falso que sempre falha, para testar isolamento de erros."""

    def collect(self):
        raise RuntimeError("Falha simulada de rede")


def fake_normalizer(raw_data):
    return [
        Article(title=item["title"], url=item["url"], source="Fake Source")
        for item in raw_data
    ]


def test_collect_all_aggregates_articles_from_multiple_sources():
    source_a = NewsSource(
        name="Fonte A",
        collector=FakeCollector([{"title": "Notícia 1", "url": "https://a.com/1"}]),
        normalizer=fake_normalizer,
    )
    source_b = NewsSource(
        name="Fonte B",
        collector=FakeCollector([{"title": "Notícia 2", "url": "https://b.com/1"}]),
        normalizer=fake_normalizer,
    )

    service = NewsCollectorService(sources=[source_a, source_b])
    articles = service.collect_all()

    assert len(articles) == 2
    assert {article.title for article in articles} == {"Notícia 1", "Notícia 2"}


def test_collect_all_ignores_failing_source_and_continues():
    working_source = NewsSource(
        name="Fonte OK",
        collector=FakeCollector([{"title": "Notícia OK", "url": "https://ok.com/1"}]),
        normalizer=fake_normalizer,
    )
    broken_source = NewsSource(
        name="Fonte Quebrada",
        collector=FailingCollector(),
        normalizer=fake_normalizer,
    )

    service = NewsCollectorService(sources=[broken_source, working_source])
    articles = service.collect_all()

    assert len(articles) == 1
    assert articles[0].title == "Notícia OK"


def test_collect_all_with_no_sources_returns_empty_list():
    service = NewsCollectorService(sources=[])
    assert service.collect_all() == []
