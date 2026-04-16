@echo off
setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

cd /d "%~dp0"

if defined BACKEND_HOST (
  set "HOST=%BACKEND_HOST%"
) else (
  set "HOST=127.0.0.1"
)

if defined BACKEND_PORT (
  set "PORT=%BACKEND_PORT%"
) else (
  set "PORT=8000"
)

if exist "venv\Scripts\python.exe" (
  set "PYTHON_EXE=%~dp0venv\Scripts\python.exe"
) else (
  set "PYTHON_EXE=python"
)

if not exist "data" mkdir data
if not exist "logs" mkdir logs

echo Backend service
echo ========================
echo Python: %PYTHON_EXE%
echo Host:   %HOST%
echo Port:   %PORT%
echo.

"%PYTHON_EXE%" -m uvicorn main:app --host %HOST% --port %PORT%
