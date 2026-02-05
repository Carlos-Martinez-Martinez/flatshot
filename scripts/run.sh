#!/bin/bash
cd "$(dirname "$0")/.."

if [ -x ".venv/bin/python" ]; then
  exec .venv/bin/python main.py
fi

if [ -x "venv/bin/python" ]; then
  exec venv/bin/python main.py
fi

exec python3 main.py
