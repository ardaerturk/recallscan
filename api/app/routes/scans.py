from fastapi import APIRouter, Depends, Header, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.config import Settings, get_settings
from api.app.db import get_session
from api.app.models.api import ManualScanRequest, ManualScanResponse
from api.app.repositories.signal_repo import recent_signals
from api.app.services.idempotency import (
    claim_idempotency_key,
    clear_idempotency_key,
    request_hash,
    store_idempotent_response,
)
from api.app.services.scan_runner import run_recent_recall_scan
from api.app.services.serializers import scan_run_out, signal_outputs
from api.app.services.utils import new_id

router = APIRouter()


@router.post("/scans", response_model=ManualScanResponse)
async def run_scan(
    payload: ManualScanRequest,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    key = idempotency_key or f"generated:{new_id('idem')}"
    if not idempotency_key:
        response.headers["X-RecallScan-Idempotency-Warning"] = "Missing Idempotency-Key; generated server-side key."
    payload_hash = request_hash(payload.model_dump(mode="json"))
    idempotency_claim = await claim_idempotency_key(session, key, payload_hash)
    if idempotency_claim == "conflict":
        raise HTTPException(status_code=409, detail="Idempotency-Key was reused with a different request body")
    if idempotency_claim == "processing":
        raise HTTPException(status_code=409, detail="Idempotency-Key is already processing")
    if idempotency_claim != "claimed":
        status_code, body = idempotency_claim
        response.status_code = status_code
        return body
    await session.commit()

    try:
        run, source_mode = await run_recent_recall_scan(
            session,
            settings,
            days=payload.days,
            force_fresh=payload.force_fresh,
            idempotency_key=key,
        )
        await session.commit()
        signals = await recent_signals(session, days=payload.days)
        result = ManualScanResponse(
            scan=scan_run_out(run),
            signals=await signal_outputs(session, signals),
            meta={"source_mode": source_mode, "idempotency_key": key},
        )
        result_json = result.model_dump(mode="json")
        await store_idempotent_response(session, key, payload_hash, 200, result_json)
        await session.commit()
        return result
    except Exception:
        await session.rollback()
        await clear_idempotency_key(session, key)
        await session.commit()
        raise
