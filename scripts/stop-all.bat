@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul

cd /d "%~dp0.."

echo Stop services
echo ========================
call :stop_port "backend" 8000
call :stop_port "frontend" 5173
call :stop_port "remote-backend" 8100
call :stop_port "remote-admin" 4173
echo Done.
goto :eof

:stop_port
set "NAME=%~1"
set "PORT=%~2"
set "PID="

for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%PORT% .*LISTENING"') do (
  set "PID=%%P"
)
if defined PID (
  echo [STOP] %NAME%  port=%PORT%  pid=!PID!
  taskkill /PID !PID! /F >nul 2>nul
  call :wait_for_port_release %PORT%
) else (
  echo [SKIP] %NAME%  port=%PORT% not running
)
set "PID="
goto :eof

:wait_for_port_release
set "WAIT_PORT=%~1"
for /L %%I in (1,1,20) do (
  netstat -ano | findstr /R /C:":%WAIT_PORT% .*LISTENING" >nul
  if errorlevel 1 exit /b 0
  >nul timeout /t 1 /nobreak
)
goto :eof
