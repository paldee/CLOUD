@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo ERROR: The virtual environment is missing. Run setup.bat first.
  exit /b 1
)
if not exist ".env" (
  echo ERROR: .env is missing. Run setup.bat first.
  exit /b 1
)

echo Using Database configuration from .env

echo Starting Backend and Frontend...
powershell -NoProfile -Command "if (Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if errorlevel 1 (
  start "Agri Backend" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"
) else (
  echo Backend is already listening on port 8000.
)

powershell -NoProfile -Command "if (Get-NetTCPConnection -State Listen -LocalPort 5173 -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if errorlevel 1 (
  start "Agri Frontend" cmd /k ".venv\Scripts\python.exe -m http.server 5173 --directory frontend"
) else (
  echo Frontend is already listening on port 5173.
)

timeout /t 2 /nobreak >nul 2>&1 || ping -n 3 127.0.0.1 >nul
start "" "http://localhost:5173"

echo Application started at http://localhost:5173
exit /b 0
