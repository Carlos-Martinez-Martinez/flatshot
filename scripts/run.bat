@echo off
cd /d "%~dp0\.."
if exist ".\.venv\Scripts\python.exe" (
    .\.venv\Scripts\python.exe main.py
    exit /b %errorlevel%
)

if exist ".\venv\Scripts\python.exe" (
    .\venv\Scripts\python.exe main.py
    exit /b %errorlevel%
)

python main.py
