"""Testes da camada de sessão: commit, rollback e tradução de erros.

Usam sessões falsas (mocks), sem qualquer dependência de um banco de
dados real — validam apenas o comportamento de `session_scope`.
"""
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError

from app.database.exceptions import DatabaseConnectionError, DatabaseTimeoutError
from app.database.session import session_scope


def _factory_returning(session: MagicMock):
    return lambda: session


def test_session_scope_commits_and_closes_on_success():
    session = MagicMock()

    with session_scope(_factory_returning(session)) as yielded_session:
        assert yielded_session is session

    session.commit.assert_called_once()
    session.rollback.assert_not_called()
    session.close.assert_called_once()


def test_session_scope_rolls_back_and_raises_connection_error():
    session = MagicMock()
    session.commit.side_effect = OperationalError("SELECT 1", {}, Exception("conexão recusada"))

    with pytest.raises(DatabaseConnectionError):
        with session_scope(_factory_returning(session)):
            pass

    session.rollback.assert_called_once()
    session.close.assert_called_once()


def test_session_scope_rolls_back_and_raises_timeout_error():
    session = MagicMock()
    session.commit.side_effect = SQLAlchemyTimeoutError("timeout ao obter conexão do pool")

    with pytest.raises(DatabaseTimeoutError):
        with session_scope(_factory_returning(session)):
            pass

    session.rollback.assert_called_once()
    session.close.assert_called_once()


def test_session_scope_rolls_back_and_reraises_other_sqlalchemy_errors():
    session = MagicMock()
    session.commit.side_effect = SQLAlchemyError("erro genérico do SQLAlchemy")

    with pytest.raises(SQLAlchemyError):
        with session_scope(_factory_returning(session)):
            pass

    session.rollback.assert_called_once()
    session.close.assert_called_once()


def test_session_scope_closes_session_even_when_body_raises():
    session = MagicMock()

    with pytest.raises(ValueError):
        with session_scope(_factory_returning(session)):
            raise ValueError("erro de negócio, não relacionado ao banco")

    session.rollback.assert_not_called()
    session.close.assert_called_once()
