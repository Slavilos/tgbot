@echo off
chcp 65001 >nul
cd /d "%~dp0"

set PYTHON=C:\Users\slavi\AppData\Local\Programs\Python\Python312\python.exe
if not exist "%PYTHON%" set PYTHON=python

echo === Проверка связи с Telegram ===
"%PYTHON%" find_proxy.py
if errorlevel 1 pause & exit /b 1

echo.
echo === Запуск бота ===
"%PYTHON%" main.py
pause
