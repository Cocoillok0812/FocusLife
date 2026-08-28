@echo off
setlocal
cd /d "%~dp0source"
if exist "%~dp0FocusLife.exe" (
  start "" "%~dp0FocusLife.exe"
  exit /b 0
)
py -3 app.py
if errorlevel 1 pause

