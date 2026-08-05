"""Ponto de entrada da aplicação TechPulse AI.

Monta as fontes de notícias configuradas, executa a coleta através do
`NewsCollectorService`, persiste os artigos novos no PostgreSQL (via
`ArticleRepository`) e imprime no terminal tanto os artigos coletados
quanto as estatísticas da execução. Ainda não há interface gráfica
nesta etapa.
"""
from __future__ import annotations

from app.collectors.devto_collector import DevToCollector
from app.collectors.github_collector import GitHubBlogCollector
from app.collectors.hackernews_collector import HackerNewsCollector
from app.collectors.rss_collector import RSSCollector
from app.config.settings import get_settings
from app.models.article import Article
from app.normalizers.devto_normalizer import normalize_devto_entries
from app.normalizers.github_normalizer import normalize_github_entries
from app.normalizers.hackernews_normalizer import normalize_hackernews_entries
from app.normalizers.rss_normalizer import normalize_rss_entries
from app.repositories.article_repository import ArticleRepository
from app.services.news_collector_service import NewsCollectorService, NewsSource


def build_service(repository: ArticleRepository | None = None) -> NewsCollectorService:
    """Monta o `NewsCollectorService` com todas as fontes da primeira etapa.

    Toda a configuração (URLs de feeds, limites de coleta) vem de
    `Settings` (`app.config.settings`), que por sua vez lê o `.env` —
    este módulo não lê nenhuma variável de ambiente diretamente.

    Args:
        repository: Repositório opcional para persistência dos artigos
            coletados (Fase 2). Se omitido, o serviço se comporta como
            na Fase 1 (`collect_all` funciona normalmente; apenas
            `collect_and_persist` exige um repositório).

    Returns:
        Instância de `NewsCollectorService` pronta para coletar.
    """
    settings = get_settings()

    sources = [
        NewsSource(
            name="TechCrunch",
            collector=RSSCollector(
                feed_url=settings.techcrunch_rss_url, source_name="TechCrunch"
            ),
            normalizer=normalize_rss_entries,
        ),
        NewsSource(
            name="GitHub Blog",
            collector=GitHubBlogCollector(feed_url=settings.github_blog_rss_url),
            normalizer=normalize_github_entries,
        ),
        NewsSource(
            name="Hacker News",
            collector=HackerNewsCollector(limit=settings.hackernews_limit),
            normalizer=normalize_hackernews_entries,
        ),
        NewsSource(
            name="Dev.to",
            collector=DevToCollector(per_page=settings.devto_per_page),
            normalizer=normalize_devto_entries,
        ),
    ]

    return NewsCollectorService(sources=sources, repository=repository)


def print_articles(articles: list[Article]) -> None:
    """Imprime os artigos coletados no terminal, para validação manual.

    Args:
        articles: Lista de `Article` a serem exibidos.
    """
    print(f"\nTotal de artigos coletados: {len(articles)}\n")
    print("-" * 80)
    for article in articles:
        published = article.published_at.isoformat() if article.published_at else "N/A"
        print(f"Título : {article.title}")
        print(f"Fonte  : {article.source}")
        print(f"Data   : {published}")
        print(f"URL    : {article.url}")
        print("-" * 80)


def main() -> None:
    """Executa a coleta, persiste os artigos e imprime resultados/estatísticas."""
    repository = ArticleRepository()
    service = build_service(repository=repository)

    result = service.collect_and_persist()
    print_articles(result.articles)
    print(result.stats.as_report())


if __name__ == "__main__":
    main()
