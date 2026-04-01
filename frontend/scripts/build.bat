@echo off
chcp 65001 >nul
setlocal

echo ========================================
echo 得物掘金工具 - 构建脚本
echo ========================================

cd /d "%~dp0\.."

echo.
echo [1/4] 安装前端依赖...
call npm install

echo.
echo [2/4] 构建前端...
call npm run build

echo.
echo [3/4] 编译 Electron...
cd electron
call npx tsc
cd ..

echo.
echo [4/4] 打包应用...
call npx electron-builder --win --x64

echo.
echo ========================================
echo 构建完成！
echo 打包文件位于: release\目录
echo ========================================
pause
