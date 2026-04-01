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

REM 启动服务
uvicorn main:app --reload --port 8000 --host 127.0.0.1
