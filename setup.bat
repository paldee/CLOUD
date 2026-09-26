@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo [1/4] Checking Python...
set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
  echo ERROR: Python 3 was not found. Install Python 3.10 or newer.
  exit /b 1
)

echo [2/4] Creating Python virtual environment...
if not exist ".venv\Scripts\python.exe" (
  %PYTHON_CMD% -m venv .venv
  if errorlevel 1 goto :failed
) else (
  echo Existing .venv found; keeping it.
)

echo [3/4] Installing Python dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
if errorlevel 1 goto :failed

echo [4/4] Preparing environment file...
if not exist ".env" (
  copy /Y ".env.example" ".env" >nul
  echo Created .env from .env.example.
) else (
  echo Existing .env found; keeping it.
)

echo Running unit tests...
".venv\Scripts\python.exe" -m pytest -q -p no:cacheprovider
if errorlevel 1 goto :failed

echo.
echo Setup completed successfully.
echo Ensure .env has valid DATABASE_URL (Amazon RDS) and GROQ_API_KEY.
echo Then run start.bat to launch the application.
exit /b 0

:failed
echo.
echo ERROR: Setup failed. Review the message above and run setup.bat again.
exit /b 1
