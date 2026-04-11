@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

echo 得物掘金工具 - 后端服务
echo ========================
cd /d "%~dp0"

REM 激活虚拟环境
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM 创建必要目录
if not exist "data" mkdir data
if not exist "logs" mkdir logs

set "BACKEND_HOST=127.0.0.1"
set "BACKEND_PORT=8000"

REM 统一走 launcher 兼容入口
set "LAUNCHER=%~dp0..\frontend\electron\launchers\start-backend-dev.bat"
if exist "%LAUNCHER%" (
    call "%LAUNCHER%" "%~dp0" %BACKEND_HOST% %BACKEND_PORT%
) else (
    echo [警告] 未找到 launcher，回退到直接 uvicorn
    uvicorn main:app --reload --port %BACKEND_PORT% --host %BACKEND_HOST%
)
