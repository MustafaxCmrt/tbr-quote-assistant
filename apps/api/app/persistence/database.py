import os

from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import create_async_engine


def database_url():
    value = os.getenv("DATABASE_URL")
    if value:
        url = make_url(value)
    else:
        url = URL.create(
            "postgresql+asyncpg",
            username=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            host=os.getenv("DB_HOST", "db"),
            port=5432,
            database=os.environ["POSTGRES_DB"],
        )
    if url.drivername != "postgresql+asyncpg":
        raise ValueError("Yalnız PostgreSQL asyncpg bağlantısı desteklenir.")
    return url


def make_engine(url=None):
    return create_async_engine(
        url or database_url(),
        pool_pre_ping=True,
        hide_parameters=True,
        connect_args={"timeout": 3, "command_timeout": 5},
    )
