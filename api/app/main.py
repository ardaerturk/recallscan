from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from asyncpg.exceptions import PostgresError

from api.app.config import get_settings
from api.app.db import ensure_schema
from api.app.routes import catalog, health, inventory, jobs, recalls, scans, suppliers


settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await ensure_schema()
    except Exception:
        logger.exception("Database schema initialization failed.")
    yield


app = FastAPI(title="RecallScan API", version="0.1.0", root_path="", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Idempotency-Key", "Authorization"],
)


def database_unavailable_response() -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Database unavailable. Check the Neon connection and project quota.",
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(_, __) -> JSONResponse:
    logger.exception("Database request failed.")
    return database_unavailable_response()


@app.exception_handler(PostgresError)
async def postgres_error_handler(_, __) -> JSONResponse:
    logger.exception("Postgres request failed.")
    return database_unavailable_response()


app.include_router(health.router, prefix="/api")
app.include_router(catalog.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(recalls.router, prefix="/api")
app.include_router(scans.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(suppliers.router, prefix="/api")
