"""Funções utilitárias para limpeza de texto vindo de fontes externas.

Centraliza remoção de HTML e normalização de espaços, para que os
normalizadores fiquem focados apenas na regra de mapeamento de campos.
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup


def remove_html(raw_html: str | None) -> str | None:
    """Remove tags HTML de uma string, mantendo apenas o texto.

    Args:
        raw_html: Texto que pode conter marcação HTML.

    Returns:
        Texto sem tags HTML, ou `None` se a entrada for `None`.
    """
    if raw_html is None:
        return None
    return BeautifulSoup(raw_html, "html.parser").get_text()


def normalize_whitespace(text: str | None) -> str | None:
    """Colapsa espaços/quebras de linha repetidos e remove espaços nas bordas.

    Args:
        text: Texto a ser normalizado.

    Returns:
        Texto com espaços normalizados, ou `None` se a entrada for `None`.
    """
    if text is None:
        return None
    return re.sub(r"\s+", " ", text).strip()


def clean_text(raw_html: str | None) -> str | None:
    """Combina remoção de HTML e normalização de espaços em um único passo.

    Args:
        raw_html: Texto bruto, possivelmente contendo HTML.

    Returns:
        Texto limpo e normalizado, ou `None` se a entrada for `None` ou vazia.
    """
    cleaned = normalize_whitespace(remove_html(raw_html))
    return cleaned or None
