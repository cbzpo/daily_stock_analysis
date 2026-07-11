@echo off
title Stock Analysis System

echo.
echo ========================================
echo   Stock Analysis System - Quick Start
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)

echo [OK] Python installed
echo.

echo Select mode:
echo   1. WebUI Dashboard
echo   2. Single Analysis
echo   3. Scheduled Task
echo   4. Debug Mode
echo.
set /p choice=Enter choice (1-4): 

echo.
if "%choice%"=="1" (
    echo [START] WebUI mode...
    echo [INFO] Visit http://192.168.222.226:9000
    python main.py --webui --host 0.0.0.0 --port 9000
) else if "%choice%"=="2" (
    echo [START] Single analysis...
    python main.py
) else if "%choice%"=="3" (
    echo [START] Scheduled mode...
    python main.py --schedule
) else if "%choice%"=="4" (
    echo [START] Debug mode...
    python main.py --debug --stocks 600519,300750,601899
) else (
    echo [INFO] Default: WebUI mode...
    python main.py --webui --host 0.0.0.0 --port 9000
)

echo.
echo [DONE]
pause
