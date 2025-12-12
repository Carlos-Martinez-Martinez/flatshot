@echo off
echo ========================================
echo   FlatShot - Instalador
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado. Instala Python 3.10+ desde python.org
    pause
    exit /b 1
)

echo [1/3] Creando entorno virtual...
python -m venv .venv

echo [2/3] Activando entorno...
call .\.venv\Scripts\activate.bat

echo [3/3] Instalando en modo desarrollo...
pip install -e .

echo.
echo ========================================
echo   Instalacion completada!
echo ========================================
echo.
echo Para ejecutar: run.bat
echo.
pause
