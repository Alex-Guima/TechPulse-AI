"""Modelo de persistência (ORM) da tabela `articles`.

Este modelo é deliberadamente separado do `Article` em
`app/models/article.py` (Pydantic): um representa o domínio da
aplicação, o outro representa exatamente como os dados são armazenados
no PostgreSQL. O `ArticleRepository` é responsável por converter entre
os dois.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ArticleModel(Base):
    """Representação persistida de um artigo na tabela `articles`.

    `external_id` armazena o identificador original da fonte (guid de
    RSS, id de história do Hacker News, id de artigo do Dev.to etc.),
    quando ela fornecer um; é sempre distinto de `id`, que é a chave
    primária autoincremento gerada pelo próprio banco.
    """

    __tablename__ = "articles"
    __table_args__ = (
        Index("ix_articles_source", "source"),
        Index("ix_articles_published_at", "published_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover - apenas para debug
        return f"ArticleModel(id={self.id!r}, title={self.title!r}, source={self.source!r})"
