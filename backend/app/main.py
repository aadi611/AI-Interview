from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings
from app.core.database import create_tables
from app.core.redis_client import close_redis
from app.api.routes import auth, sessions, recordings, admin
from app.api.websockets.interview_ws import interview_ws_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    recordings_dir = Path(settings.STORAGE_LOCAL_PATH)
    recordings_dir.mkdir(parents=True, exist_ok=True)
    yield
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST routes
app.include_router(auth.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(recordings.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

# Serve recordings as static files
recordings_path = Path(settings.STORAGE_LOCAL_PATH)
recordings_path.mkdir(parents=True, exist_ok=True)
app.mount("/recordings", StaticFiles(directory=str(recordings_path)), name="recordings")


# WebSocket endpoint — unified for both voice (audio) and chat (text)
@app.websocket("/ws/interview/{session_id}")
async def interview_websocket(websocket: WebSocket, session_id: str):
    await interview_ws_handler.handle(websocket, session_id)


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}
