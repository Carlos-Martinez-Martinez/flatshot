from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SMOKE_SCRIPT = PROJECT_ROOT / "scripts" / "visual_regression_smoke.py"


def test_frontend_visual_regression_smoke_checks_visual_landmarks_and_assets():
    result = subprocess.run(
        [sys.executable, str(SMOKE_SCRIPT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "frontend_visual_regression_smoke OK" in result.stdout
