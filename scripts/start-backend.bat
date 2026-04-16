@echo off
setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

cd /d "%~dp0.."

echo Local backend
echo ========================
echo Root: %CD%
echo.

call backend\run.bat
