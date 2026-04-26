@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul

cd /d "%~dp0.."

echo Service status
echo ========================
call :print_status "backend" 8000 "http://127.0.0.1:8000"
call :print_status "frontend" 5173 "http://localhost:5173"
call :print_status "remote-backend" 8100 "http://127.0.0.1:8100"
call :print_status "remote-admin" 4173 "http://127.0.0.1:4173/dist-react/react-index.html?apiBase=http://127.0.0.1:8100 (legacy: /index.html?apiBase=http://127.0.0.1:8100)"
goto :eof

:print_status
set "NAME=%~1"
set "PORT=%~2"
set "URL=%~3"
set "PID="
set "PROC="

for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%PORT% .*LISTENING"') do (
  set "PID=%%P"
)
if defined PID (
  for /f "skip=3 tokens=1" %%I in ('tasklist /FI "PID eq !PID!"') do (
    if not defined PROC set "PROC=%%I"
  )
  echo [RUNNING] %NAME%  port=%PORT%  pid=!PID!  process=!PROC!
  echo           %URL%
) else (
  echo [STOPPED] %NAME%  port=%PORT%
  echo           %URL%
)
echo.
set "PID="
set "PROC="
goto :eof
