@echo off
REM ============================================
REM  DSA API Service Restart
REM  Run as Administrator if kill fails.
REM  Bind: 127.0.0.1:8000 (localhost only)
REM ============================================
echo === DSA API Service Restart ===
echo.

REM --- 1. Kill any process listening on port 8000 ---
echo [1/3] Stopping old service on port 8000...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":8000"') do (
    echo       Killing PID %%p
    taskkill /PID %%p /F
)

REM --- 2. Wait for port release ---
echo [2/3] Waiting for port release...
timeout /t 3 /nobreak >nul

REM --- 3. Start service ---
echo [3/3] Starting API on 127.0.0.1:8000 ...
cd /d D:\mimocode\daily_stock_analysis
start "DSA-API" "%USERPROFILE%\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" server.py

echo.
echo === Done ===
echo Service is starting up (first load takes ~10s).
echo Open in Edge (NOT 360 browser): http://127.0.0.1:8000/docs
echo If kill failed above, re-run this script as Administrator.
echo.
pause
