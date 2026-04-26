@echo off
setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

cd /d "%~dp0.."

set "REMOTE_BACKEND_URL=http://127.0.0.1:8100"
set "REMOTE_ADMIN_URL=http://127.0.0.1:4173/dist-react/index.html?apiBase=http://127.0.0.1:8100"

echo Remote one-click
echo ========================
echo Remote backend: %REMOTE_BACKEND_URL%
echo Remote admin  : %REMOTE_ADMIN_URL%
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python not found.
  exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] npm not found.
  exit /b 1
)

if not exist "frontend\node_modules" (
  echo [INFO] Installing shared frontend dependencies...
  pushd frontend
  call npm install
  if errorlevel 1 (
    popd
    exit /b 1
  )
  popd
)

echo [INFO] Building remote-admin...
call npm --prefix remote\remote-admin run build
if errorlevel 1 exit /b 1
call npm --prefix remote\remote-admin run build:react
if errorlevel 1 exit /b 1

echo [INFO] Bootstrapping remote admin account...
set "BOOTSTRAP_ADMIN_PASSWORD=admin-secret"
pushd remote\remote-backend
python scripts/bootstrap_admin.py --migrate --username admin --password-env BOOTSTRAP_ADMIN_PASSWORD --role super_admin --display-name "Remote Admin"
if errorlevel 1 (
  popd
  exit /b 1
)
popd

netstat -ano | findstr /R /C:":8100 .*LISTENING" >nul
if errorlevel 1 (
  echo [INFO] Starting remote-backend in a new window...
  start "mydw-remote-backend" cmd /k "cd /d %CD%\remote\remote-backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8100"
) else (
  echo [INFO] Remote-backend already listening on 8100.
)

netstat -ano | findstr /R /C:":4173 .*LISTENING" >nul
if errorlevel 1 (
  echo [INFO] Starting remote-admin static server in a new window...
  start "mydw-remote-admin" cmd /k "cd /d %CD% && python -m http.server 4173 --bind 127.0.0.1 --directory remote/remote-admin"
) else (
  echo [INFO] Remote-admin static server already listening on 4173.
)

echo.
echo [INFO] Open %REMOTE_ADMIN_URL%
echo [INFO] Multi-user users update smoke: npm --prefix remote\remote-admin run smoke:users:update:multi
start "" "%REMOTE_ADMIN_URL%"
