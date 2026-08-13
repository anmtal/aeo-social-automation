@echo off
chcp 65001 >nul
cd /d "%~dp0"
python "tools\linkedin_today.py"
echo.
pause
