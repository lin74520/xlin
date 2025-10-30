@echo off
chcp 65001 >nul
echo ========================================
echo 小林AI小说
echo 构建EXE文件
echo ========================================
echo.

echo 正在检查PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller未安装，正在安装...
    pip install pyinstaller
)

echo.
echo 开始构建EXE文件...
echo 这可能需要几分钟时间，请耐心等待...
echo.

python build.py

echo.
echo ========================================
echo 构建完成！
echo EXE文件位于 dist 目录下
echo ========================================
echo.
pause
