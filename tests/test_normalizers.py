"""Testes unitários dos normalizadores de cada fonte."""
from app.normalizers.devto_normalizer import normalize_devto_entries
from app.normalizers.github_normalizer import normalize_github_entries
from app.normalizers.hackernews_normalizer import normalize_hackernews_entries
from app.normalizers.rss_normalizer import normalize_rss_entries


def test_normalize_rss_entries_maps_fields_correctly():
    raw_entries = [
        {
            "source": "TechCrunch",
            "title": "<b>Nova IA</b> lançada",
            "link": "https://techcrunch.com/noticia",
            "author": "Jane Doe",
            "published": "Mon, 01 Jan 2024 12:00:00 +0000",
            "summary": "Resumo <i>com html</i>",
            "content": "Conteúdo completo",
            "tags": ["ai", "startups"],
            "id": "tc-1",
        }
    ]

    articles = normalize_rss_entries(raw_entries)

    assert len(articles) == 1
    article = articles[0]
    assert article.title == "Nova IA lançada"
    assert article.source == "TechCrunch"
    assert article.summary == "Resumo com html"
    assert article.tags == ["ai", "startups"]
    assert article.published_at is not None
    assert article.external_id == "tc-1"
    assert article.id is None


def test_normalize_github_entries_reuses_rss_normalizer():
    raw_entries = [
        {
            "source": "GitHub Blog",
            "title": "Novidades do GitHub",
            "link": "https://github.blog/noticia",
            "author": None,
            "published": "Mon, 01 Jan 2024 12:00:00 +0000",
            "summary": "Resumo",
            "content": None,
            "tags": [],
            "id": "gh-1",
        }
    ]

    articles = normalize_github_entries(raw_entries)

    assert len(articles) == 1
    assert articles[0].source == "GitHub Blog"
    assert articles[0].external_id == "gh-1"


def test_normalize_hackernews_entries_skips_items_without_title():
    raw_items = [
        {"id": 1, "title": "Título válido", "url": None, "by": "user1", "time": 1704110400},
        {"id": 2, "title": None},
        {},
    ]

    articles = normalize_hackernews_entries(raw_items)

    assert len(articles) == 1
    assert articles[0].title == "Título válido"
    assert articles[0].url == "https://news.ycombinator.com/item?id=1"
    assert articles[0].source == "Hacker News"
    assert articles[0].external_id == "1"
    assert articles[0].id is None


def test_normalize_devto_entries_maps_fields_correctly():
    raw_items = [
        {
            "id": 42,
            "title": "Artigo Dev.to",
            "url": "https://dev.to/artigo",
            "user": {"name": "Autor Dev"},
            "published_at": "2024-01-01T12:00:00Z",
            "description": "Descrição curta",
            "tag_list": ["python", "webdev"],
        }
    ]

    articles = normalize_devto_entries(raw_items)

    assert len(articles) == 1
    article = articles[0]
    assert article.title == "Artigo Dev.to"
    assert article.author == "Autor Dev"
    assert article.tags == ["python", "webdev"]
    assert article.source == "Dev.to"
    assert article.external_id == "42"
    assert article.id is None
