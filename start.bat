@echo off
cd /d "%~dp0"
title Douyin Downloader - Portable

echo =============================================
echo   Douyin Video Downloader - Portable Version
echo =============================================
echo.

:: Detect Python
set PYTHON_CMD=
where python >nul 2>&1
if "%errorlevel%"=="0" (
    set PYTHON_CMD=python
) else (
    where py >nul 2>&1
    if "%errorlevel%"=="0" (
        set PYTHON_CMD=py -3
    )
)

if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python not found!
    echo.
    echo Please install Python 3.8+ first:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: Check dependencies
echo [*] Checking dependencies...
%PYTHON_CMD% -c "import flask" >nul 2>&1
if "%errorlevel%" neq "0" (
    echo [*] Installing Flask...
    %PYTHON_CMD% -m pip install flask -q
    if "%errorlevel%" neq "0" (
        echo [ERROR] Failed to install Flask!
        pause
        exit /b 1
    )
    echo [OK] Flask installed.
)
echo [OK] All dependencies ready.
echo.

:: Kill previous instance
netstat -ano | findstr ":5001" >nul 2>&1
if "%errorlevel%"=="0" (
    echo [*] Stopping previous instance...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5001" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
    timeout /t 2 >nul
)

echo [*] Starting server in new window...
start "Douyin Downloader" %PYTHON_CMD% -u app.py

:: Wait for server to start
timeout /t 2 /nobreak >nul

:: Open browser
echo [*] Opening browser...
start http://127.0.0.1:5001
echo.
echo [*] Server is running in the other window.
echo [*] Close the "Douyin Downloader" window to stop.
echo.
pause