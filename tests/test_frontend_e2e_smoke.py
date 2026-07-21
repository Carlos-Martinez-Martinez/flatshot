from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SMOKE_SCRIPT = PROJECT_ROOT / "scripts" / "e2e_smoke.py"


def test_frontend_e2e_smoke_serves_app_and_linked_assets():
    result = subprocess.run(
        [sys.executable, str(SMOKE_SCRIPT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "frontend_e2e_smoke OK" in result.stdout
