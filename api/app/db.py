from collections.abc import AsyncGenerator
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from api.app.config import get_settings


def _database_config() -> tuple[str, dict[str, bool]]:
    settings = get_settings()
    url = settings.database_url.strip().strip('"').strip("'")
    connect_args = {"ssl": True} if _requires_ssl(url) else {}
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return _strip_asyncpg_unsupported_query_params(url), connect_args


def _strip_asyncpg_unsupported_query_params(url: str) -> str:
    parsed = urlsplit(url)
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key not in {"channel_binding", "sslmode"}
    ]
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query and urlencode(query), parsed.fragment))


def _requires_ssl(url: str) -> bool:
    values = {key: value.lower() for key, value in parse_qsl(urlsplit(url).query)}
    return values.get("sslmode") in {"require", "verify-ca", "verify-full"}


DATABASE_URL, DATABASE_CONNECT_ARGS = _database_config()

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    connect_args=DATABASE_CONNECT_ARGS,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def ensure_schema() -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                create table if not exists schema_migrations (
                  version text primary key,
                  applied_at timestamptz not null default now()
                )
                """
            )
        )
        applied = set((await conn.execute(text("select version from schema_migrations"))).scalars().all())
        for migration in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if migration.name in applied:
                continue
            for statement in _split_sql(migration.read_text()):
                await conn.execute(text(statement))
            await conn.execute(
                text("insert into schema_migrations (version) values (:version)"),
                {"version": migration.name},
            )


def _split_sql(sql: str) -> list[str]:
    return [statement.strip() for statement in sql.split(";") if statement.strip()]
