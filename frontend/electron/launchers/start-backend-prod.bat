@echo off
setlocal

set "BACKEND_ROOT=%~1"

if "%BACKEND_ROOT%"=="" set "BACKEND_ROOT=%BACKEND_ROOT%"
if "%BACKEND_ROOT%"=="" (
  echo BACKEND_ROOT is required
  exit /b 1
)

cd /d "%BACKEND_ROOT%"
call "%BACKEND_ROOT%\backend.exe"
