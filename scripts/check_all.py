"""Run FlatShot's local validation checks."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHECKS = (
    (sys.executable, "-m", "pytest"),
    (sys.executable, "-m", "ruff", "check", "."),
    (sys.executable, "scripts/audit_css.py", "--check"),
    (sys.executable, "scripts/check_application_answers.py"),
    (sys.executable, "scripts/e2e_smoke.py"),
    (sys.executable, "scripts/visual_regression_smoke.py"),
)


def main() -> int:
    for command in CHECKS:
        print(f"\n$ {' '.join(command)}", flush=True)
        result = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
        if result.returncode != 0:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
