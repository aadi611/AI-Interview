@echo off
echo Starting InterviewAI...

start "InterviewAI - Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"
timeout /t 2 /nobreak >nul
start "InterviewAI - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo.
echo Both servers are starting in separate windows.
pause
