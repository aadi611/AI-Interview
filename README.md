# InterviewAI — Full-Stack AI Interview Platform

A production-grade AI interview platform with real-time voice + chat, video recording, multi-domain intelligence, and LangGraph-powered adaptive questioning.

### Screenshots

### Home Page
![Home Page](homepage.jpg)

### Dashboard
![Dashboard](dashboard.jpg)

### Interview
![Interview](interiew.jpg)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND  (Next.js 14)                        │
│  Landing → Auth → Dashboard → Setup → Interview Room → Results       │
│  State: Zustand │ UI: shadcn/ui + Tailwind │ Motion: Framer Motion   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  REST + WebSocket
┌──────────────────────────────▼──────────────────────────────────────┐
│                        BACKEND  (FastAPI)                             │
│  REST API (/auth, /sessions, /recordings)                            │
│  WebSocket (/ws/interview/:id, /ws/voice/:id)                        │
│  LangGraph Engine (onboarding → questions → eval → feedback)         │
│  LLM Adapters: OpenAI │ Claude │ Ollama                              │
│  Speech: Whisper STT │ ElevenLabs/gTTS TTS                           │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│  PostgreSQL (users, sessions, results)  │  Redis (session state)     │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Prerequisites

Install these before starting:

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.11+ | https://python.org |
| Node.js | 20+ | https://nodejs.org |
| PostgreSQL | 15+ | https://postgresql.org/download |
| Redis | 7+ | https://redis.io/download (Windows: use Redis Stack or WSL) |

> **Windows Redis tip:** Download the latest `.msi` from https://github.com/microsoftarchive/redis/releases — or run Redis inside WSL2.

---

## Local Setup

### 1. Create the database

Open `psql` or pgAdmin and run:

```sql
CREATE DATABASE ai_interview;
```

### 2. Configure the backend

```bash
cd backend
copy .env.example .env
```

Open `backend/.env` and fill in:

```env
OPENAI_API_KEY=sk-...          # your OpenAI key
OPENAI_MODEL=gpt-4.5-preview   # or any model you have access to

DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/ai_interview
REDIS_URL=redis://localhost:6379
SECRET_KEY=any-random-long-string
```

### 3. Install Python dependencies

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Start the backend

```bash
# Make sure venv is active
uvicorn app.main:app --reload --port 8000
```

API docs available at http://localhost:8000/docs

### 5. Configure the frontend

```bash
cd frontend
copy .env.local.example .env.local
```

`.env.local` should contain:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### 6. Install frontend dependencies

```bash
cd frontend
npm install
```

### 7. Start the frontend

```bash
npm run dev
```

App runs at http://localhost:3000

---

## One-Click Startup (Windows)

Use the included `start.bat` in the project root.

What `start.bat` does:
- Detects `winget` and attempts to install missing tools: Python, Node.js LTS, PostgreSQL, Redis-compatible Memurai
- Starts PostgreSQL/Redis services if available
- Creates `backend/.env` and `frontend/.env.local` from example files when missing
- Creates `backend/venv` and installs backend requirements
- Runs `npm install` in `frontend`
- Tries to create database `ai_interview`
- Starts backend and frontend in separate terminal windows

Run:
```bat
start.bat
```

Or just double-click `start.bat` in File Explorer.

Notes for first run:
- Some installations/service operations may require running as Administrator
- PostgreSQL setup may prompt for credentials during installation
- You still need to set API keys in `backend/.env` for LLM/speech features
- If `winget` is unavailable, install dependencies manually once (Python, Node, PostgreSQL, Redis)

---

## Switching LLM Provider

Edit `backend/.env` — no code changes needed:

```env
# OpenAI (default)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.5-preview

# Switch to Claude
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-...

# Switch to local Ollama
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

---

## Adding a New Interview Domain

Add one entry to `backend/app/domains/registry.py`:

```python
MY_DOMAIN = DomainConfig(
    name="my_domain",
    display_name="My Custom Domain",
    description="Short description shown in the UI",
    topics=["topic1", "topic2"],
    evaluation_criteria=["criterion1", "criterion2"],
)
DOMAIN_REGISTRY["my_domain"] = MY_DOMAIN
```

Questions are AI-generated from the config — no question bank needed.

---

## LangGraph Interview Flow

```
START
  └─► onboarding
        └─► generate_questions  (5 adaptive questions via LLM)
              └─► [wait for answer]
                    └─► evaluate_answer
                          ├─► follow_up  (if incomplete, max 2×)
                          └─► ask_next_question
                                └─► ... repeat ...
                                      └─► generate_feedback → END
```

Adaptive difficulty: 2 correct in a row → harder; 2 wrong → easier.

---

## WebSocket Protocol

### Chat (`/ws/interview/:id`)
```
Client → { "type": "message", "content": "..." }
Server → { "type": "message", "content": "...", "role": "assistant" }
Server → { "type": "typing",  "active": true }
Server → { "type": "evaluation", "data": { score, strengths, ... } }
```

### Voice (`/ws/voice/:id`)
```
Client → { "type": "start_voice" }
Client → <binary audio chunks (WebM/Opus)>
Client → { "type": "end_voice" }
Server → { "type": "transcript", "text": "..." }
Server → { "type": "audio", "data": "<base64 mp3>" }
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TailwindCSS, Framer Motion, Zustand |
| Backend | FastAPI, Python 3.12, WebSockets |
| AI Orchestration | LangGraph, LangChain Core |
| Default LLM | OpenAI (adapter pattern — swap via env) |
| Speech STT | OpenAI Whisper |
| Speech TTS | gTTS (default) / ElevenLabs |
| Database | PostgreSQL + SQLAlchemy async |
| Session State | Redis |
| Recording | MediaRecorder API → local storage / S3 |
| Auth | JWT + bcrypt |
