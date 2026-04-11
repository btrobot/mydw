@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

echo ========================================
echo 得物掘金工具 - 启动脚本
echo ========================================

cd /d "%~dp0"

REM 检查虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo [1/4] 激活虚拟环境...
    call venv\Scripts\activate.bat
) else (
    echo [1/4] 使用系统 Python...
)

REM 安装依赖
echo [2/4] 检查依赖...
pip install -r requirements.txt >nul 2>&1

REM 安装 Playwright 浏览器
echo [3/4] 安装 Playwright 浏览器...
python -m playwright install chromium >nul 2>&1
if errorlevel 1 (
    echo 警告: Playwright 浏览器安装可能失败，请手动运行: python -m playwright install chromium
)

REM 创建必要目录
echo [4/4] 创建必要目录...
if not exist "data" mkdir data
if not exist "logs" mkdir logs

echo.
echo ========================================
echo 依赖安装完成！
echo ========================================
echo.
echo 推荐启动后端服务:
echo   .\run.bat
echo.
echo 如需仅测试 Python 入口，也可运行:
echo   python main.py
echo.
pause
