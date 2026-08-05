"""Context manager central para uso de sessões do SQLAlchemy.

Este é o único lugar do projeto que faz commit, rollback e close de uma
sessão. Erros de baixo nível do SQLAlchemy são traduzidos para exceções
específicas da aplicação (`app.database.exceptions`); nenhum outro
ponto do código deve capturar exceções genéricas do SQLAlchemy.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Optional

from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError
from sqlalchemy.orm import Session, sessionmaker

from app.database.engine import get_session_factory
from app.database.exceptions import DatabaseConnectionError, DatabaseTimeoutError


@contextmanager
def session_scope(session_factory: Optional[sessionmaker] = None) -> Iterator[Session]:
    """Fornece uma sessão transacional, com commit/rollback automáticos.

    Args:
        session_factory: Fábrica de sessões a ser usada. Se omitida,
            usa a fábrica padrão da aplicação (`get_session_factory`).
            Parâmetro existe principalmente para permitir injeção de
            uma fábrica de testes, apontando para um banco de teste.

    Yields:
        Uma sessão SQLAlchemy pronta para uso.

    Raises:
        DatabaseConnectionError: se ocorrer falha de conexão/comunicação
            com o banco (ex: banco fora do ar).
        DatabaseTimeoutError: se a operação exceder o tempo limite
            (ex: timeout ao obter conexão do pool).
        SQLAlchemyError: para qualquer outro erro do SQLAlchemy não
            coberto pelos casos acima (ex: violação de integridade),
            repassado para que o chamador decida como tratar.
    """
    factory = session_factory or get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except SQLAlchemyTimeoutError as error:
        session.rollback()
        raise DatabaseTimeoutError(
            f"Tempo limite excedido ao acessar o banco de dados: {error}"
        ) from error
    except OperationalError as error:
        session.rollback()
        raise DatabaseConnectionError(
            f"Falha de conexão com o banco de dados: {error}"
        ) from error
    except SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.close()
