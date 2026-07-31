"""Funções utilitárias para conversão de datas vindas de fontes externas.

Cada fonte representa datas de um jeito diferente (string RFC 822,
timestamp Unix, ISO 8601...). Este módulo centraliza essa conversão para
que os normalizadores não precisem lidar com `datetime` diretamente.
"""
from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional, Union


def parse_date(value: Optional[Union[str, int, float]]) -> Optional[datetime]:
    """Converte um valor de data em diversos formatos para `datetime`.

    Suporta:
        - Timestamps Unix (int/float), como os usados pelo Hacker News.
        - Strings no formato RFC 822/2822, comuns em feeds RSS.
        - Strings ISO 8601, comuns em APIs REST (ex: Dev.to).

    Args:
        value: Valor bruto de data vindo da fonte externa.

    Returns:
        Um `datetime` (UTC) ou `None` se `value` for `None` ou não puder
        ser interpretado.
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None

        try:
            return parsedate_to_datetime(value)
        except (TypeError, ValueError):
            pass

        try:
            iso_value = value.replace("Z", "+00:00")
            return datetime.fromisoformat(iso_value)
        except ValueError:
            return None

    return None
