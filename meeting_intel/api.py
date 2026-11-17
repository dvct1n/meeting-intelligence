"""FastAPI service.  Run:  uvicorn meeting_intel.api:app --reload"""
from __future__ import annotations

import logging
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse

from . import __version__
from .config import get_settings
from .export import to_markdown
from .schemas import Meeting, SearchHit, SearchRequest
from .services import Services, get_services

log = logging.getLogger(__name__)

ALLOWED = {".wav", ".mp3", ".m4a", ".mp4", ".flac", ".ogg", ".webm", ".mkv"}
CHUNK = 1024 * 1024


@asynccontextmanager
async def lifespan(_: FastAPI):
    logging.basicConfig(
        level=getattr(logging, get_settings().log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:  # jobs that were running when the server stopped can never finish: mark them failed
        fixed = get_services().store.recover_interrupted()
        if fixed:
            log.warning("marked %d interrupted meeting(s) as failed: %s", len(fixed), fixed)
    except Exception:  # pragma: no cover - never block start-up on housekeeping
        log.exception("start-up recovery failed")
    yield


app = FastAPI(
    title="AI Meeting Intelligence",
    version=__version__,
    description="Turn meeting recordings into transcripts, decisions, action items and semantic search.",
    lifespan=lifespan,
)


def require_api_key(
    svc: Services = Depends(get_services),
    x_api_key: str | None = Header(default=None),
) -> None:
    """Optional auth: enforced only when the API_KEY environment variable is set."""
    expected = svc.settings.api_key
    if expected and not (x_api_key and secrets.compare_digest(x_api_key, expected)):
        raise HTTPException(401, "Invalid or missing API key")


@app.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok", "version": __version__}


protected = APIRouter(dependencies=[Depends(require_api_key)])


@protected.post("/meetings", response_model=Meeting, status_code=202, tags=["meetings"])
def upload_meeting(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    svc: Services = Depends(get_services),
) -> Meeting:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(400, f"Unsupported file type '{suffix}'. Allowed: {sorted(ALLOWED)}")

    max_bytes = svc.settings.max_upload_mb * CHUNK
    meeting_id = svc.store.new_id()
    filename = f"audio{suffix}"
    written = 0
    try:
        with open(svc.store.dir(meeting_id) / filename, "wb") as out:
            while chunk := file.file.read(CHUNK):
                written += len(chunk)
                if written > max_bytes:
                    raise HTTPException(413, f"File too large (limit {svc.settings.max_upload_mb} MB)")
                out.write(chunk)
        if written == 0:
            raise HTTPException(400, "Empty file")
    except HTTPException:
        svc.store.delete(meeting_id)  # do not leave a partial upload behind
        raise

    meeting = Meeting(id=meeting_id, filename=filename)
    svc.store.save(meeting)
    background.add_task(svc.pipeline.process, meeting_id)
    return meeting


@protected.get("/meetings", response_model=list[Meeting], tags=["meetings"])
def list_meetings(svc: Services = Depends(get_services)) -> list[Meeting]:
    # lightweight listing: drop the heavy transcript fields
    return [m.model_copy(update={"utterances": [], "chunks": []}) for m in svc.store.list()]


@protected.get("/meetings/{meeting_id}", response_model=Meeting, tags=["meetings"])
def get_meeting(meeting_id: str, svc: Services = Depends(get_services)) -> Meeting:
    try:
        return svc.store.load(meeting_id)
    except FileNotFoundError:
        raise HTTPException(404, "Meeting not found") from None


@protected.get("/meetings/{meeting_id}/export", response_class=PlainTextResponse, tags=["meetings"])
def export_meeting(meeting_id: str, svc: Services = Depends(get_services)) -> PlainTextResponse:
    """The whole meeting (summary, decisions, action items, transcript) as Markdown."""
    try:
        meeting = svc.store.load(meeting_id)
    except FileNotFoundError:
        raise HTTPException(404, "Meeting not found") from None
    return PlainTextResponse(to_markdown(meeting), media_type="text/markdown; charset=utf-8")


@protected.delete("/meetings/{meeting_id}", status_code=204, tags=["meetings"])
def delete_meeting(meeting_id: str, svc: Services = Depends(get_services)) -> None:
    try:
        meeting = svc.store.load(meeting_id)
    except FileNotFoundError:
        raise HTTPException(404, "Meeting not found") from None
    if meeting.status in ("uploaded", "processing"):
        raise HTTPException(409, "Meeting is still being processed")
    svc.index.delete_meeting(meeting_id)
    svc.store.delete(meeting_id)


@protected.post("/search", response_model=list[SearchHit], tags=["search"])
def search(req: SearchRequest, svc: Services = Depends(get_services)) -> list[SearchHit]:
    if not req.query.strip():
        raise HTTPException(400, "Empty query")
    return svc.index.search(req.query, meeting_id=req.meeting_id, limit=req.limit)


app.include_router(protected)
