@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0"
cd /d "%ROOT%"

echo =========================================================
echo   InterviewAI Windows Bootstrap
echo =========================================================
echo.

where winget >nul 2>nul
if errorlevel 1 (
	echo [WARN] winget not found. Auto-install of tools may be skipped.
) else (
	echo [OK] winget detected.
)

call :install_if_missing python "Python.Python.3.12" "Python 3.12"
call :install_if_missing node "OpenJS.NodeJS.LTS" "Node.js LTS"
call :install_if_missing psql "PostgreSQL.PostgreSQL" "PostgreSQL"

call :install_redis_if_missing
call :start_postgres_service
call :start_redis_service

echo.
echo [STEP] Creating env files if missing...
if not exist "%ROOT%backend\.env" (
	copy /Y "%ROOT%backend\.env.example" "%ROOT%backend\.env" >nul
	echo [OK] Created backend\.env from example.
) else (
	echo [OK] backend\.env already exists.
)

if not exist "%ROOT%frontend\.env.local" (
	if exist "%ROOT%frontend\.env.local.example" (
		copy /Y "%ROOT%frontend\.env.local.example" "%ROOT%frontend\.env.local" >nul
		echo [OK] Created frontend\.env.local from example.
	) else (
		echo [WARN] frontend\.env.local.example not found. Skipping frontend env creation.
	)
) else (
	echo [OK] frontend\.env.local already exists.
)

echo.
echo [STEP] Setting up Python virtual environment...
if not exist "%ROOT%backend\venv\Scripts\python.exe" (
	where py >nul 2>nul
	if not errorlevel 1 (
		py -3 -m venv "%ROOT%backend\venv"
	) else (
		python -m venv "%ROOT%backend\venv"
	)
)

if not exist "%ROOT%backend\venv\Scripts\python.exe" (
	echo [ERROR] Could not create backend virtual environment.
	echo         Check Python installation and rerun this script.
	goto :end
)

echo [STEP] Installing backend requirements...
call "%ROOT%backend\venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r "%ROOT%backend\requirements.txt"
if errorlevel 1 (
	echo [ERROR] Backend dependency installation failed.
	goto :end
)

echo.
echo [STEP] Installing frontend npm dependencies...
cd /d "%ROOT%frontend"
npm install
if errorlevel 1 (
	echo [ERROR] Frontend npm install failed.
	goto :end
)

cd /d "%ROOT%"
echo.
echo [STEP] Attempting to create PostgreSQL database: ai_interview
where psql >nul 2>nul
if errorlevel 1 (
	echo [WARN] psql not found. Skipping DB creation.
) else (
	call :create_db_if_missing
)

echo.
echo [STEP] Starting backend and frontend...
start "InterviewAI - Backend" cmd /k "cd /d ""%ROOT%backend"" && call venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8000"
timeout /t 2 /nobreak >nul
start "InterviewAI - Frontend" cmd /k "cd /d ""%ROOT%frontend"" && npm run dev"

echo.
echo =========================================================
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo =========================================================
echo.
echo If backend fails to connect DB/Redis, edit backend\.env and verify:
echo - DATABASE_URL
echo - REDIS_URL
echo.
goto :end

:install_if_missing
set "CMD_NAME=%~1"
set "WINGET_ID=%~2"
set "DISPLAY_NAME=%~3"

where %CMD_NAME% >nul 2>nul
if not errorlevel 1 (
	echo [OK] %DISPLAY_NAME% already installed.
	goto :eof
)

where winget >nul 2>nul
if errorlevel 1 (
	echo [WARN] %DISPLAY_NAME% missing and winget unavailable.
	goto :eof
)

echo [STEP] Installing %DISPLAY_NAME% via winget...
winget install -e --id %WINGET_ID% --accept-source-agreements --accept-package-agreements
if errorlevel 1 (
	echo [WARN] winget install failed for %DISPLAY_NAME%. Install it manually.
) else (
	echo [OK] Installed %DISPLAY_NAME%.
)
goto :eof

:install_redis_if_missing
where redis-server >nul 2>nul
if not errorlevel 1 (
	echo [OK] Redis already installed.
	goto :eof
)

where winget >nul 2>nul
if errorlevel 1 (
	echo [WARN] Redis missing and winget unavailable.
	goto :eof
)

echo [STEP] Installing Redis-compatible server (Memurai Developer) via winget...
winget install -e --id Memurai.MemuraiDeveloper --accept-source-agreements --accept-package-agreements
if errorlevel 1 (
	echo [WARN] Redis install failed. Please install Redis/Redis Stack manually.
) else (
	echo [OK] Installed Memurai Developer.
)
goto :eof

:start_postgres_service
echo [STEP] Starting PostgreSQL service (if installed)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "& { $svc = Get-Service | Where-Object { $_.Name -match 'postgres' -or $_.DisplayName -match 'PostgreSQL' } | Select-Object -First 1; if ($svc) { if ($svc.Status -ne 'Running') { Start-Service -Name $svc.Name }; Write-Host '[OK] PostgreSQL service:' $svc.Name } else { Write-Host '[WARN] PostgreSQL service not found.' } }"
goto :eof

:start_redis_service
echo [STEP] Starting Redis service (if installed)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "& { $svc = Get-Service | Where-Object { $_.Name -match 'redis|memurai' -or $_.DisplayName -match 'Redis|Memurai' } | Select-Object -First 1; if ($svc) { if ($svc.Status -ne 'Running') { Start-Service -Name $svc.Name }; Write-Host '[OK] Redis service:' $svc.Name } else { Write-Host '[WARN] Redis service not found.' } }"
goto :eof

:create_db_if_missing
set "DBNAME=ai_interview"
for /f "delims=" %%A in ('psql -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname=''%DBNAME%'';" 2^>nul') do set "DB_EXISTS=%%A"
if "%DB_EXISTS%"=="1" (
	echo [OK] Database %DBNAME% already exists.
	goto :eof
)

echo [STEP] Creating database %DBNAME% (may prompt for postgres password)...
psql -U postgres -c "CREATE DATABASE %DBNAME%;" >nul 2>nul
if errorlevel 1 (
	echo [WARN] Could not auto-create %DBNAME%. Create it manually if needed.
) else (
	echo [OK] Database %DBNAME% created.
)
goto :eof

:end
echo.
echo Bootstrap script finished.
pause
endlocal
