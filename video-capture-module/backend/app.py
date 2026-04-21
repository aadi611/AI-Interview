from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_int(value: str, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


STORAGE_DIR = Path(os.getenv("VIDEO_STORAGE_DIR", "./data/recordings")).resolve()
CHUNKS_DIR = Path(os.getenv("VIDEO_CHUNKS_DIR", "./data/chunks")).resolve()
MAX_FILE_BYTES = _safe_int(os.getenv("VIDEO_MAX_FILE_MB", "512"), 512) * 1024 * 1024
INDEX_FILE = STORAGE_DIR / "index.json"

STORAGE_DIR.mkdir(parents=True, exist_ok=True)
CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
if not INDEX_FILE.exists():
    INDEX_FILE.write_text("{}", encoding="utf-8")


class SessionCreateResponse(BaseModel):
    session_id: str
    created_at: str


class SessionMetadata(BaseModel):
    session_id: str
    created_at: str
    updated_at: str
    status: str
    original_filename: str | None = None
    mime_type: str | None = None
    extension: str | None = None
    size_bytes: int | None = None
    storage_path: str | None = None
    chunk_count: int = 0


app = FastAPI(title="Video Capture Backend", version="1.0.0")

allowed_origins_raw = os.getenv("VIDEO_ALLOWED_ORIGINS", "*")
allowed_origins = [v.strip() for v in allowed_origins_raw.split(",") if v.strip()]
if not allowed_origins:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _read_index() -> dict[str, Any]:
    try:
        return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_index(data: dict[str, Any]) -> None:
    INDEX_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _guess_ext(filename: str | None, content_type: str | None) -> str:
    if filename and "." in filename:
        return "." + filename.rsplit(".", 1)[-1].lower()
    mapping = {
        "video/webm": ".webm",
        "video/mp4": ".mp4",
        "video/quicktime": ".mov",
        "video/x-matroska": ".mkv",
        "video/ogg": ".ogv",
    }
    return mapping.get((content_type or "").lower(), ".webm")


def _ensure_session(session_id: str) -> dict[str, Any]:
    index = _read_index()
    if session_id not in index:
        raise HTTPException(status_code=404, detail="Session not found")
    return index


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "time": _now_iso()}


@app.post("/sessions", response_model=SessionCreateResponse)
def create_session() -> SessionCreateResponse:
    session_id = str(uuid4())
    now = _now_iso()

    index = _read_index()
    index[session_id] = {
        "session_id": session_id,
        "created_at": now,
        "updated_at": now,
        "status": "created",
        "original_filename": None,
        "mime_type": None,
        "extension": None,
        "size_bytes": None,
        "storage_path": None,
        "chunk_count": 0,
    }
    _write_index(index)

    (CHUNKS_DIR / session_id).mkdir(parents=True, exist_ok=True)
    return SessionCreateResponse(session_id=session_id, created_at=now)


@app.post("/sessions/{session_id}/upload", response_model=SessionMetadata)
async def upload_full_file(session_id: str, file: UploadFile = File(...)) -> SessionMetadata:
    index = _ensure_session(session_id)
    ext = _guess_ext(file.filename, file.content_type)
    out_path = STORAGE_DIR / f"{session_id}{ext}"

    written = 0
    with out_path.open("wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            written += len(chunk)
            if written > MAX_FILE_BYTES:
                out_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="File too large")
            f.write(chunk)

    now = _now_iso()
    index[session_id].update(
        {
            "updated_at": now,
            "status": "uploaded",
            "original_filename": file.filename,
            "mime_type": file.content_type,
            "extension": ext,
            "size_bytes": written,
            "storage_path": str(out_path),
        }
    )
    _write_index(index)

    return SessionMetadata(**index[session_id])


@app.post("/sessions/{session_id}/chunk", response_model=SessionMetadata)
async def upload_chunk(
    session_id: str,
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    file: UploadFile = File(...),
) -> SessionMetadata:
    index = _ensure_session(session_id)
    if chunk_index < 0 or total_chunks <= 0 or chunk_index >= total_chunks:
        raise HTTPException(status_code=400, detail="Invalid chunk index/total")

    session_chunk_dir = CHUNKS_DIR / session_id
    session_chunk_dir.mkdir(parents=True, exist_ok=True)
    chunk_path = session_chunk_dir / f"{chunk_index:08d}.part"

    size = 0
    with chunk_path.open("wb") as f:
        while True:
            data = await file.read(1024 * 1024)
            if not data:
                break
            size += len(data)
            f.write(data)

    meta = index[session_id]
    meta["status"] = "chunking"
    meta["updated_at"] = _now_iso()
    meta["chunk_count"] = max(meta.get("chunk_count", 0), chunk_index + 1)
    meta["original_filename"] = meta.get("original_filename") or file.filename
    meta["mime_type"] = meta.get("mime_type") or file.content_type
    meta["_total_chunks"] = total_chunks

    _write_index(index)
    return SessionMetadata(**{k: v for k, v in meta.items() if not k.startswith("_")})


@app.post("/sessions/{session_id}/finalize", response_model=SessionMetadata)
def finalize_chunks(session_id: str) -> SessionMetadata:
    index = _ensure_session(session_id)
    meta = index[session_id]

    session_chunk_dir = CHUNKS_DIR / session_id
    if not session_chunk_dir.exists():
        raise HTTPException(status_code=400, detail="No chunks found for session")

    chunk_files = sorted(session_chunk_dir.glob("*.part"))
    if not chunk_files:
        raise HTTPException(status_code=400, detail="No chunk files to finalize")

    total_expected = meta.get("_total_chunks")
    if isinstance(total_expected, int) and len(chunk_files) < total_expected:
        raise HTTPException(status_code=400, detail="Missing chunks; cannot finalize")

    ext = _guess_ext(meta.get("original_filename"), meta.get("mime_type"))
    out_path = STORAGE_DIR / f"{session_id}{ext}"

    total_size = 0
    with out_path.open("wb") as out:
        for chunk in chunk_files:
            with chunk.open("rb") as part:
                shutil.copyfileobj(part, out)
            total_size += chunk.stat().st_size
            if total_size > MAX_FILE_BYTES:
                out_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="Final file too large")

    for chunk in chunk_files:
        chunk.unlink(missing_ok=True)
    session_chunk_dir.rmdir()

    meta.update(
        {
            "updated_at": _now_iso(),
            "status": "uploaded",
            "extension": ext,
            "size_bytes": total_size,
            "storage_path": str(out_path),
        }
    )
    meta.pop("_total_chunks", None)
    _write_index(index)

    return SessionMetadata(**meta)


@app.get("/sessions", response_model=list[SessionMetadata])
def list_sessions() -> list[SessionMetadata]:
    index = _read_index()
    sessions = []
    for value in index.values():
        cleaned = {k: v for k, v in value.items() if not k.startswith("_")}
        sessions.append(SessionMetadata(**cleaned))
    sessions.sort(key=lambda x: x.updated_at, reverse=True)
    return sessions


@app.get("/sessions/{session_id}", response_model=SessionMetadata)
def get_session(session_id: str) -> SessionMetadata:
    index = _ensure_session(session_id)
    cleaned = {k: v for k, v in index[session_id].items() if not k.startswith("_")}
    return SessionMetadata(**cleaned)


@app.get("/sessions/{session_id}/download")
def download_session_file(session_id: str) -> FileResponse:
    index = _ensure_session(session_id)
    meta = index[session_id]
    storage_path = meta.get("storage_path")
    if not storage_path:
        raise HTTPException(status_code=404, detail="No file uploaded for session")

    path = Path(storage_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Stored file missing")

    filename = meta.get("original_filename") or path.name
    media_type = meta.get("mime_type") or "application/octet-stream"
    return FileResponse(path=path, filename=filename, media_type=media_type)


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str) -> dict[str, str]:
    index = _ensure_session(session_id)
    meta = index.pop(session_id)

    path = meta.get("storage_path")
    if path:
        Path(path).unlink(missing_ok=True)

    chunk_dir = CHUNKS_DIR / session_id
    if chunk_dir.exists():
        for p in chunk_dir.glob("*.part"):
            p.unlink(missing_ok=True)
        chunk_dir.rmdir()

    _write_index(index)
    return {"status": "deleted", "session_id": session_id}
