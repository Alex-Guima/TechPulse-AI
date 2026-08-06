"""Coletor do GitHub Blog.

O GitHub Blog expõe um feed RSS, então esta classe apenas especializa o
`RSSCollector` genérico com a URL correta. Manter um arquivo próprio
permite, no futuro, trocar a estratégia de coleta (ex: migrar para uma
API oficial do GitHub) sem impactar outras fontes que também usam RSS.
"""
from __future__ import annotations

from techpulse_ai.collectors.rss_collector import RSSCollector

GITHUB_BLOG_FEED_URL = "https://github.blog/feed/"


class GitHubBlogCollector(RSSCollector):
    """Coleta postagens do GitHub Blog via seu feed RSS."""

    def __init__(self, feed_url: str = GITHUB_BLOG_FEED_URL) -> None:
        super().__init__(feed_url=feed_url, source_name="GitHub Blog")
