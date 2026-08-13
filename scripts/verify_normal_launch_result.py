"""Validate evidence collected from a normal frozen FlatShot launch."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _mapping(payload: dict[str, Any], name: str) -> dict[str, Any]:
    value = payload.get(name)
    if not isinstance(value, dict):
        raise RuntimeError(f"normal-launch result is missing {name}")
    return value


def validate_result(payload: dict[str, Any]) -> None:
    failures: list[str] = []
    if payload.get("collectorErrors"):
        failures.append("collector reported errors")
    process = _mapping(payload, "process")
    environment = _mapping(payload, "environment")
    http = _mapping(payload, "http")
    frontend = _mapping(http, "frontend")
    bridge = _mapping(http, "bridge")
    window = _mapping(payload, "window")
    webview = _mapping(payload, "webView2")
    runtime_log = _mapping(payload, "runtimeLog")
    screenshot = _mapping(payload, "screenshot")
    ui_automation = _mapping(payload, "uiAutomation")
    cleanup = _mapping(payload, "cleanup")

    if payload.get("schemaVersion") != 1:
        failures.append("unsupported normal-launch result schema")
    if not process.get("started"):
        failures.append("process did not start")
    if not process.get("stayedAlive"):
        failures.append("process did not stay alive")
    if frontend.get("status") != 200:
        failures.append("frontend did not return HTTP 200")
    if bridge.get("status") != 200:
        failures.append("bridge health did not return HTTP 200")
    if not window.get("visible"):
        failures.append("visible FlatShot window was not found")
    if not isinstance(window.get("handle"), int) or window["handle"] <= 0:
        failures.append("window handle is zero")
    if "flatshot" not in str(window.get("title", "")).casefold():
        failures.append("window title does not identify FlatShot")
    if not webview.get("detected") or not webview.get("temporallyRelated"):
        failures.append("WebView2 was not detected for this launch")
    if payload.get("windowMode") != "edgechromium native window" or runtime_log.get("fallbackDetected"):
        failures.append("native EdgeChromium window was not used")
    if runtime_log.get("startupErrors"):
        failures.append("startup errors were logged")
    if not isinstance(screenshot.get("sizeBytes"), int) or screenshot["sizeBytes"] <= 0:
        failures.append("screenshot artifact is empty")
    if not ui_automation.get("contentDetected"):
        failures.append("FlatShot WebView2 content control was not detected")
    if cleanup.get("flatShotOrphans"):
        failures.append("FlatShot processes remained after cleanup")
    if cleanup.get("listenerPortsRemaining"):
        failures.append("listeners remained after cleanup")
    for key, label in (
        ("pythonHomeCleared", "PYTHONHOME was not cleared"),
        ("pythonPathCleared", "PYTHONPATH was not cleared"),
        ("virtualEnvCleared", "VIRTUAL_ENV was not cleared"),
        ("pathSanitized", "child PATH was not sanitized"),
        ("executableInPortableRoot", "executable was not inside the extracted portable root"),
    ):
        if not environment.get(key):
            failures.append(label)
    if environment.get("externalPythonProcesses"):
        failures.append("external Python process was started")

    if failures:
        raise RuntimeError("Normal launch verification failed: " + "; ".join(failures))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = json.loads(args.result.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise RuntimeError("normal-launch result root must be an object")
        validate_result(payload)
    except (OSError, json.JSONDecodeError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"Normal launch evidence verified: {args.result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
