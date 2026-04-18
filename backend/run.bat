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

set "LAUNCHER=%~dp0..\frontend\electron\launchers\start-backend-dev.bat"

echo Backend service
echo ========================
echo Python: %PYTHON_EXE%
echo Host:   %HOST%
echo Port:   %PORT%
echo.

if exist "%LAUNCHER%" (
  call "%LAUNCHER%" "%~dp0" "%HOST%" "%PORT%"
  exit /b %errorlevel%
)

"%PYTHON_EXE%" -m uvicorn main:app --host %HOST% --port %PORT%
