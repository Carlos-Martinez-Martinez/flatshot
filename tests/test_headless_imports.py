import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

HEADLESS_MODULES = [
    "flatshot.core",
    "flatshot.core.engine",
    "flatshot.core.models",
    "flatshot.core.overrides",
    "flatshot.core.scaling",
    "flatshot.application",
    "flatshot.application.app_state",
    "flatshot.application.contracts",
    "flatshot.application.events",
    "flatshot.application.execution_control",
    "flatshot.application.export_config_service",
    "flatshot.application.export_run_planner",
    "flatshot.application.export_runner",
    "flatshot.application.folder_scanner",
    "flatshot.application.presenters",
    "flatshot.application.preset_service",
    "flatshot.application.preview_service",
    "flatshot.application.queue_runner",
    "flatshot.application.session_service",
    "flatshot.application.settings_service",
]


def test_core_and_application_modules_import_headlessly_without_qt():
    code = f"""
import importlib
import sys

modules = {json.dumps(HEADLESS_MODULES)}
for module_name in modules:
    importlib.import_module(module_name)

qt_modules = sorted(
    name for name in sys.modules
    if name == "PyQt6" or name.startswith("PyQt6.")
)
if qt_modules:
    raise SystemExit("Unexpected PyQt imports: " + ", ".join(qt_modules[:20]))
"""
    env = os.environ.copy()
    src_path = str(PROJECT_ROOT / "src")
    env["PYTHONPATH"] = (
        src_path
        if not env.get("PYTHONPATH")
        else src_path + os.pathsep + env["PYTHONPATH"]
    )

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr or result.stdout
