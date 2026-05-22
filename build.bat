@echo off
cd /d "%~dp0"

echo Building...
echo.

if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

py -m PyInstaller --onefile --windowed --name "douyin" --icon "icon.ico" --add-data "templates;templates" app.py

if exist "dist\douyin.exe" (
    echo Build complete!
    echo.
    echo Output: %~dp0dist\douyin.exe
    echo.
    pause
)
