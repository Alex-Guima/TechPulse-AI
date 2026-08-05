"""Exceções específicas da camada de persistência.

Usadas para traduzir erros de baixo nível do SQLAlchemy/PostgreSQL em
erros com significado claro para o restante da aplicação, evitando o
uso de `except Exception` genérico em qualquer ponto do código.
"""
from __future__ import annotations


class DatabaseError(Exception):
    """Erro base para qualquer falha na camada de persistência."""


class DatabaseConnectionError(DatabaseError):
    """Falha ao conectar ou se comunicar com o banco de dados."""


class DatabaseTimeoutError(DatabaseError):
    """Uma operação no banco de dados excedeu o tempo limite esperado."""


class ArticleInsertError(DatabaseError):
    """Falha ao inserir um artigo por um motivo que não é duplicidade de URL."""
