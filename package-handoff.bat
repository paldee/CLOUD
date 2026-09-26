@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist ".env" (
  echo ERROR: .env was not found. Configure it before creating the handoff ZIP.
  exit /b 1
)

echo WARNING: This package will contain .env, API keys, and database credentials.
echo Share it only with authorized team members through a trusted channel.
echo Rotate the API keys if the ZIP is sent to the wrong recipient.
echo.
set /P "CONFIRM=Type INCLUDE to continue: "
if /I not "%CONFIRM%"=="INCLUDE" (
  echo Packaging cancelled.
  exit /b 1
)

for /F %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "TIMESTAMP=%%T"
set "OUTPUT=%~dp0..\CLOUD-handoff-%TIMESTAMP%.zip"

echo Creating handoff package...
tar.exe -a -cf "%OUTPUT%" ^
  --exclude=./.git ^
  --exclude=./.venv ^
  --exclude=./node_modules ^
  --exclude=node_modules ^
  --exclude=./tmp ^
  --exclude=./.pytest_cache ^
  --exclude=./.mypy_cache ^
  --exclude=./.ruff_cache ^
  --exclude=__pycache__ ^
  --exclude=*.pyc ^
  --exclude=*.log ^
  .
if errorlevel 1 (
  echo ERROR: Failed to create the ZIP package.
  exit /b 1
)

tar.exe -tf "%OUTPUT%" | findstr /X /C:"./.env" >nul
if errorlevel 1 (
  echo ERROR: The ZIP was created but .env was not included.
  exit /b 1
)

echo.
echo Handoff package created successfully:
echo %OUTPUT%
echo.
echo The receiving team can extract it, run setup.bat, and then run start.bat.
exit /b 0
