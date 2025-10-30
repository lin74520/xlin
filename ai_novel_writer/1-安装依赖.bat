@echo off
chcp 65001 >nul
echo ========================================
echo 小林AI小说
echo 安装依赖包
echo ========================================
echo.

echo 正在安装依赖包，请稍候...
echo.

pip install -r requirements.txt

echo.
echo ========================================
echo 安装完成！
echo 现在可以运行 "2-运行程序.bat" 启动程序
echo ========================================
echo.
pause
