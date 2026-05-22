@echo off
cd /d "%~dp0"
title Douyin Downloader

netstat -ano | findstr ":5001" >nul 2>&1
if "%errorlevel%"=="0" (
    echo Stopping previous instance...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5001" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
    timeout /t 2 >nul
)

start http://127.0.0.1:5001
"C:\Users\Liuyanbo\AppData\Local\Python\pythoncore-3.14-64\python.exe" -u app.py
