"""Run the local FlatShot bridge from a source checkout."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "src"
if SRC_ROOT.exists():
    sys.path.insert(0, str(SRC_ROOT))

from flatshot.bridge.http_server import main


if __name__ == "__main__":
    raise SystemExit(main())
