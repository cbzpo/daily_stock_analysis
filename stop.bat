@echo off
title Stop Stock Analysis

echo.
echo ========================================
echo   Stop Stock Analysis System
echo ========================================
echo.

echo [STOP] Stopping services...

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":9000.*LISTENING"') do (
    echo [INFO] Found process on port 9000: PID %%a
    taskkill /F /PID %%a 2>nul
    if not errorlevel 1 (
        echo [OK] Stopped process %%a
    )
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":9001.*LISTENING"') do (
    echo [INFO] Found process on port 9001: PID %%a
    taskkill /F /PID %%a 2>nul
    if not errorlevel 1 (
        echo [OK] Stopped process %%a
    )
)

echo.
echo [DONE] Services stopped
echo.
pause
