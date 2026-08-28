@echo off
setlocal
cd /d "%~dp0source"
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name FocusLife app.py
if errorlevel 1 pause

