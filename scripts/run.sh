#!/bin/bash
cd "$(dirname "$0")/.."

if [ -x ".venv/bin/python" ]; then
  exec .venv/bin/python apps/flatshot-desktop/run_dev.py --open
fi

if [ -x "venv/bin/python" ]; then
  exec venv/bin/python apps/flatshot-desktop/run_dev.py --open
fi

exec python3 apps/flatshot-desktop/run_dev.py --open
