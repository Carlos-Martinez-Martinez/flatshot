import json

import pytest

from scripts.verify_normal_launch_result import validate_result


def valid_result() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "executable": r"D:\Fresh path á\FlatShotPortable\FlatShot.exe",
        "portableRoot": r"D:\Fresh path á\FlatShotPortable",
        "collectorErrors": [],
        "process": {"started": True, "stayedAlive": True, "exitCodeBeforeCleanup": None},
        "environment": {
            "pythonHomeCleared": True,
            "pythonPathCleared": True,
            "virtualEnvCleared": True,
            "pathSanitized": True,
            "executableInPortableRoot": True,
            "externalPythonProcesses": [],
        },
        "http": {
            "frontend": {"status": 200, "url": "http://127.0.0.1:4173/"},
            "bridge": {"status": 200, "url": "http://127.0.0.1:8765/health"},
        },
        "window": {"visible": True, "title": "FlatShot", "handle": 12345},
        "webView2": {"detected": True, "temporallyRelated": True, "pids": [12346]},
        "windowMode": "edgechromium native window",
        "runtimeLog": {"fallbackDetected": False, "startupErrors": []},
        "screenshot": {
            "path": r"D:\evidence\flatshot-normal-launch.png",
            "sizeBytes": 84521,
            "nonUniform": True,
            "width": 1360,
            "height": 900,
            "clientContentDetected": True,
        },
        "cleanup": {
            "gracefulCloseRequested": True,
            "forceKillUsed": False,
            "flatShotOrphans": [],
            "listenerPortsRemaining": [],
        },
    }


def test_accepts_complete_native_edgechromium_launch_evidence():
    validate_result(valid_result())


@pytest.mark.parametrize(
    ("mutate", "expected_message"),
    [
        (lambda data: data["process"].update(stayedAlive=False), "process did not stay alive"),
        (lambda data: data["http"]["frontend"].update(status=503), "frontend did not return HTTP 200"),
        (lambda data: data["http"]["bridge"].update(status=503), "bridge health did not return HTTP 200"),
        (lambda data: data["window"].update(visible=False), "visible FlatShot window was not found"),
        (lambda data: data["window"].update(handle=0), "window handle is zero"),
        (lambda data: data["webView2"].update(detected=False), "WebView2 was not detected"),
        (lambda data: data.update(windowMode="browser fallback"), "native EdgeChromium window was not used"),
        (lambda data: data["runtimeLog"].update(startupErrors=["Traceback"]), "startup errors were logged"),
        (lambda data: data["screenshot"].update(nonUniform=False), "screenshot is empty or uniform"),
        (lambda data: data["screenshot"].update(clientContentDetected=False), "WebView2 client content was not captured"),
        (lambda data: data["cleanup"].update(flatShotOrphans=[4321]), "FlatShot processes remained"),
        (lambda data: data["cleanup"].update(listenerPortsRemaining=[4173]), "listeners remained"),
        (lambda data: data["environment"].update(pathSanitized=False), "child PATH was not sanitized"),
        (
            lambda data: data["environment"].update(externalPythonProcesses=[{"name": "python.exe", "pid": 77}]),
            "external Python process was started",
        ),
        (lambda data: data.update(collectorErrors=["PrintWindow failed"]), "collector reported errors"),
    ],
)
def test_rejects_missing_normal_launch_gate(mutate, expected_message):
    result = valid_result()
    mutate(result)

    with pytest.raises(RuntimeError, match=expected_message):
        validate_result(result)


def test_cli_rejects_fallback_evidence(tmp_path):
    from scripts.verify_normal_launch_result import main

    result = valid_result()
    result["runtimeLog"]["fallbackDetected"] = True
    result["windowMode"] = "browser fallback"
    result_path = tmp_path / "normal-launch-result.json"
    result_path.write_text(json.dumps(result), encoding="utf-8")

    assert main([str(result_path)]) == 1
