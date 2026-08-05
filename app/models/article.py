"""Modelo de domínio único para representar uma notícia de tecnologia.

Todas as fontes de dados (RSS, APIs de terceiros, etc.) são convertidas
para este modelo pelos normalizadores, garantindo que o restante do
sistema nunca precise conhecer o formato original de cada fonte.

Desde a Fase 2, `id` e `external_id` têm significados distintos: `id`
é sempre a chave primária atribuída pelo banco de dados (preenchida
pelo `ArticleRepository`), enquanto `external_id` é o identificador
original da notícia na fonte (quando ela fornecer um), atribuído pelos
normalizadores. Um `Article` recém-normalizado, antes de ser
persistido, sempre tem `id=None`.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Article(BaseModel):
    """Representa uma notícia padronizada, independente da origem.

    Campos ausentes na fonte original devem ser preenchidos com ``None``
    (ou lista vazia, no caso de ``tags``) pelos normalizadores — nunca
    omitidos.
    """

    id: Optional[str] = Field(
        default=None,
        description=(
            "Identificador do artigo na camada de persistência (chave "
            "primária do banco). Preenchido pelo `ArticleRepository` ao "
            "ler/gravar um artigo; nunca é definido pelos "
            "normalizadores. Para o identificador original da fonte, "
            "ver `external_id`."
        ),
    )
    external_id: Optional[str] = Field(
        default=None,
        description=(
            "Identificador original do artigo na fonte de origem (ex: "
            "guid de um item RSS, id de uma história no Hacker News), "
            "quando ela fornecer um. Preenchido pelos normalizadores; "
            "distinto de `id`, que é sempre a chave primária no banco."
        ),
    )
    title: str = Field(description="Título da notícia.")
    url: str = Field(description="URL original da notícia.")
    author: Optional[str] = Field(
        default=None, description="Autor da notícia, se informado pela fonte."
    )
    published_at: Optional[datetime] = Field(
        default=None, description="Data/hora de publicação, já convertida para datetime."
    )
    source: str = Field(description="Nome da fonte de origem (ex: 'TechCrunch', 'Hacker News').")
    summary: Optional[str] = Field(
        default=None, description="Resumo curto da notícia, quando fornecido pela fonte."
    )
    content: Optional[str] = Field(
        default=None, description="Conteúdo completo ou parcial da notícia, se disponível."
    )
    tags: List[str] = Field(
        default_factory=list, description="Lista de tags/categorias associadas à notícia."
    )

    class Config:
        frozen = False
        str_strip_whitespace = True
