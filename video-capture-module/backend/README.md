# Video Capture Backend (Streamlit Integratable)

Standalone FastAPI backend for video recording workflows. This folder is isolated and does not change your existing project structure.

## Features
- Create recording sessions
- Upload full recording files
- Upload recording chunks + finalize
- List sessions and metadata
- Download recording by session
- Delete sessions/files
- CORS enabled for easy Streamlit integration

## Quick Start
```bash
cd video-capture-module/backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8010 --reload
```

## API
- `GET /health`
- `POST /sessions`
- `POST /sessions/{session_id}/upload` (full file)
- `POST /sessions/{session_id}/chunk` (chunk uploads)
- `POST /sessions/{session_id}/finalize` (assemble chunks)
- `GET /sessions`
- `GET /sessions/{session_id}`
- `GET /sessions/{session_id}/download`
- `DELETE /sessions/{session_id}`

## Streamlit Integration (Example)
Use any streamlit video component/uploader and send file bytes:

```python
import requests
import streamlit as st

API = "http://localhost:8010"

if "session_id" not in st.session_state:
    resp = requests.post(f"{API}/sessions", timeout=20)
    resp.raise_for_status()
    st.session_state.session_id = resp.json()["session_id"]

video_file = st.file_uploader("Upload Interview Recording", type=["webm", "mp4", "mov", "mkv"])
if video_file is not None:
    files = {"file": (video_file.name, video_file.getvalue(), video_file.type or "video/webm")}
    r = requests.post(f"{API}/sessions/{st.session_state.session_id}/upload", files=files, timeout=120)
    r.raise_for_status()
    st.success("Uploaded")
```

## Notes
- For browser-side live recording, your Streamlit UI can record locally (custom component) and either:
  1. Upload one full file to `/upload`, or
  2. Send chunks to `/chunk` then call `/finalize`.
- Metadata is persisted in `data/recordings/index.json`.
