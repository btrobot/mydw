@echo off
setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

cd /d "%~dp0.."

echo Frontend one-click
echo ========================
echo Frontend URL: http://localhost:5173
echo Backend URL : http://127.0.0.1:8000
echo.

where node >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js not found.
  exit /b 1
)

if not exist "frontend\node_modules" (
  echo [INFO] Installing frontend dependencies...
  pushd frontend
  call npm install
  if errorlevel 1 (
    popd
    exit /b 1
  )
  popd
)

if not exist "backend\venv\Scripts\python.exe" (
  echo [ERROR] backend venv missing. Run dev.bat or create backend\venv first.
  exit /b 1
)

netstat -ano | findstr /R /C:":8000 .*LISTENING" >nul
if errorlevel 1 (
  echo [INFO] Starting backend in a new window...
  start "mydw-backend" cmd /k "cd /d %CD% && call scripts\start-backend.bat"
) else (
  echo [INFO] Backend already listening on 8000.
)

netstat -ano | findstr /R /C:":5173 .*LISTENING" >nul
if not errorlevel 1 (
  echo [INFO] Frontend already listening on 5173.
  echo [INFO] Open http://localhost:5173
  exit /b 0
)

echo [INFO] Starting frontend dev server in current window...
pushd frontend
call npm run dev
popd
