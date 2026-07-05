from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_SCRIPT = PROJECT_ROOT / "scripts" / "benchmark_shadow_v2.py"


def test_benchmark_smoke_mode_runs_small_render_case(tmp_path):
    output_path = tmp_path / "benchmark.json"

    result = subprocess.run(
        [
            sys.executable,
            str(BENCHMARK_SCRIPT),
            "--smoke",
            "--runs",
            "1",
            "--json",
            str(output_path),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "120x160 small white clean" in result.stdout

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload[0]["case"] == {
        "size": "120x160",
        "product": "small",
        "background": "white",
        "alpha": "clean",
    }
    for metric in ("shadow_pure", "preview_complete", "export_complete_no_save"):
        assert payload[0][metric]["median_ms"] >= 0
        assert payload[0][metric]["p95_ms"] >= 0
