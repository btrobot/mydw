@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

echo ========================================
echo 得物掘金工具 - 启动脚本
echo ========================================

cd /d "%~dp0"

REM 检查 Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到 Node.js，请先安装
    pause
    exit /b 1
)

REM 检查 Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装
    pause
    exit /b 1
)

echo.
echo [1/4] 检查依赖...

REM 安装前端依赖
if not exist "frontend\node_modules" (
    echo [2/4] 安装前端依赖...
    cd frontend
    call npm install
    cd ..
)

REM 安装后端依赖
if not exist "backend\venv" (
    echo [3/4] 创建虚拟环境并安装后端依赖...
    cd backend
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
    python -m playwright install chromium
    cd ..
) else (
    echo [3/4] 后端依赖已安装
)

REM 创建目录
if not exist "backend\data" mkdir backend\data
if not exist "backend\logs" mkdir backend\logs

echo.
echo ========================================
echo 启动开发模式
echo ========================================
echo.
echo 前端地址: http://localhost:5173
echo 后端地址: http://localhost:8000
echo API文档:  http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo.

REM 启动后端（统一走 backend\run.bat）
start "后端服务" cmd /c "cd /d %~dp0backend && call run.bat"

REM 启动前端
cd frontend
call npm run dev

pause
