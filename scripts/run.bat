@echo off
cd /d "%~dp0\.."
if exist ".\.venv\Scripts\python.exe" (
    .\.venv\Scripts\python.exe apps\flatshot-desktop\run_dev.py --open
    exit /b %errorlevel%
)

if exist ".\venv\Scripts\python.exe" (
    .\venv\Scripts\python.exe apps\flatshot-desktop\run_dev.py --open
    exit /b %errorlevel%
)

python apps\flatshot-desktop\run_dev.py --open
