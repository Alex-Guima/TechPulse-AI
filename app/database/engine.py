"""Criação (lazy) do engine e da session factory do SQLAlchemy.

O engine só é criado na primeira vez que for efetivamente necessário
(primeira chamada a `get_session_factory`), evitando que a simples
importação deste módulo tente abrir conexão com o banco — importante
para que módulos como `app.main` possam ser importados mesmo sem um
PostgreSQL disponível (ex: em testes que não usam banco).
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import get_settings

_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None


def get_engine() -> Engine:
    """Cria (uma única vez) e retorna o engine do SQLAlchemy."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            echo=settings.database_echo,
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory() -> sessionmaker:
    """Cria (uma única vez) e retorna a session factory padrão da aplicação."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            expire_on_commit=False,
            class_=Session,
        )
    return _session_factory
