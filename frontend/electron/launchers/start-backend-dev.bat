@echo off
setlocal

set "BACKEND_ROOT=%~1"
set "BACKEND_HOST=%~2"
set "BACKEND_PORT=%~3"

if "%BACKEND_ROOT%"=="" set "BACKEND_ROOT=%BACKEND_ROOT%"
if "%BACKEND_HOST%"=="" set "BACKEND_HOST=127.0.0.1"
if "%BACKEND_PORT%"=="" set "BACKEND_PORT=8000"

set "PYTHON_BIN=%BACKEND_ROOT%\venv\Scripts\python.exe"
if not exist "%PYTHON_BIN%" set "PYTHON_BIN=python"

cd /d "%BACKEND_ROOT%"
call "%PYTHON_BIN%" -m uvicorn main:app --port %BACKEND_PORT% --host %BACKEND_HOST%
