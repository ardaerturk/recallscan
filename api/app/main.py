from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.app.config import get_settings
from api.app.db import ensure_schema
from api.app.routes import catalog, health, inventory, jobs, recalls, scans, suppliers


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await ensure_schema()
    yield


app = FastAPI(title="RecallScan API", version="0.1.0", root_path="", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Idempotency-Key", "Authorization"],
)


app.include_router(health.router, prefix="/api")
app.include_router(catalog.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(recalls.router, prefix="/api")
app.include_router(scans.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(suppliers.router, prefix="/api")
