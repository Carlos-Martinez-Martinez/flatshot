@echo off
setlocal
set "SCRIPT_DIR=%~dp0"

if "%~1"=="" (
  python "%SCRIPT_DIR%run_dev.py" --open
) else (
  python "%SCRIPT_DIR%run_dev.py" %*
)
