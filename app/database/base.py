"""Base declarativa do SQLAlchemy 2.0, compartilhada por todos os modelos ORM."""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Classe base para todos os modelos de persistência (ORM) do projeto."""
