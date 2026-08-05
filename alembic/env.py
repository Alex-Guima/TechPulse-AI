"""Script de ambiente do Alembic.

Integra as migrations com a configuração centralizada do projeto
(`app.config.settings.Settings`) e com a metadata declarativa
(`app.database.base.Base`), permitindo autogenerate e garantindo que a
URL de conexão venha sempre do `.env`, nunca hardcoded no `alembic.ini`.
"""
from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# Garante que o pacote `app` seja importável quando o Alembic é
# executado a partir da raiz do projeto.
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config.settings import get_settings  # noqa: E402
from app.database.base import Base  # noqa: E402
from app.database import models  # noqa: E402,F401  garante que ArticleModel seja registrado

# Objeto de configuração do Alembic, que dá acesso aos valores do
# arquivo .ini em uso.
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Sobrescreve a URL do banco com a configuração centralizada da
# aplicação (lida do .env via Pydantic Settings), em vez de depender
# de um valor fixo no alembic.ini.
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

# Metadata usada pelo Alembic para detectar mudanças no autogenerate.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Executa migrations em modo 'offline' (gera SQL sem conectar ao banco)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Executa migrations em modo 'online' (conectando de fato ao banco)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
