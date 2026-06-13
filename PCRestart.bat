@echo off
cd /d "%~dp0"
call PCStop.bat
timeout /t 1 /nobreak >nul
call PCRun.bat
