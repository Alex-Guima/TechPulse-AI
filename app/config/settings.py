"""Configuração centralizada da aplicação, usando Pydantic Settings.

Lê variáveis do `.env` existente na raiz do projeto. As variáveis de
coleta da Fase 1 têm valores padrão para manter compatibilidade com o
comportamento atual (ver `app/main.py`); as novas variáveis de banco de
dados (Fase 2) não possuem padrões sensíveis para produção e devem ser
definidas no `.env` local.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação, carregadas do ambiente/`.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Coleta (Fase 1) ---
    techcrunch_rss_url: str = "https://techcrunch.com/feed/"
    github_blog_rss_url: str = "https://github.blog/feed/"
    hackernews_limit: int = 20
    devto_per_page: int = 20

    # --- Banco de dados (Fase 2) ---
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "techpulse"
    database_user: str = "postgres"
    database_password: str = "postgres"
    database_echo: bool = False

    @property
    def database_url(self) -> str:
        """Monta a URL de conexão do SQLAlchemy para o PostgreSQL."""
        return (
            f"postgresql+psycopg2://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )


@lru_cache
def get_settings() -> Settings:
    """Retorna uma instância única (cacheada) de `Settings`."""
    return Settings()
