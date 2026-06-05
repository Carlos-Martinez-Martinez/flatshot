#!/bin/bash
echo "========================================"
echo "  FlatShot Desktop - Instalador Mac/Linux"
echo "========================================"
echo

cd "$(dirname "$0")/.."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 no encontrado. Instálalo desde python.org"
    exit 1
fi

echo "[1/3] Creando entorno virtual..."
python3 -m venv .venv

echo "[2/3] Activando entorno..."
source .venv/bin/activate

echo "[3/3] Instalando en modo desarrollo..."
pip install -e .

echo
echo "========================================"
echo "  Instalación completada!"
echo "========================================"
echo
echo "Para ejecutar: ./scripts/run.sh"
echo
