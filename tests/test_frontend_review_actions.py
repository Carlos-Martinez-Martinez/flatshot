import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "app-review-actions.js"


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend action checks")
def test_open_output_folder_uses_bridge_endpoint_for_real_batches():
    script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

global.state = {{
  exportDestinations: ["C:/Batch/Salida"],
  exportResult: null,
  statusText: "",
}};
global.exportResultViewHelpers = {{
  outputDestinationToOpen(options) {{
    return options.exportDestinations[0] || "";
  }},
}};
global.isBridgeBatch = () => true;
global.bridgeErrorMessage = (error) => error.message;
const bridgeCalls = [];
global.bridgeRequest = async (path, options) => {{
  bridgeCalls.push({{ path, body: JSON.parse(options.body), method: options.method }});
  return {{ ok: true, path: "C:/Batch/Salida" }};
}};
let renders = 0;
global.render = () => {{ renders += 1; }};
global.window = {{
  open() {{
    throw new Error("file fallback should not be used for bridge batches");
  }},
}};
global.formatterHelpers = {{
  pathToFileUrl(path) {{ return `file:///${{path}}`; }},
}};

vm.runInThisContext(fs.readFileSync({json.dumps(str(HELPER_PATH))}, "utf8"));

(async () => {{
  await openOutputFolder();
  assert.deepEqual(bridgeCalls, [
    {{ path: "/folders/open", method: "POST", body: {{ path: "C:/Batch/Salida" }} }},
  ]);
  assert.equal(state.statusText, "Carpeta de salida abierta");
  assert.equal(renders, 1);
}})().catch((error) => {{
  console.error(error);
  process.exitCode = 1;
}});
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend action checks")
def test_output_browser_actions_open_grouped_folder_and_reveal_file():
    script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

global.state = {{
  exportDestinations: ["C:/Batch/Salida"],
  exportResult: null,
  outputBrowserOpen: false,
  statusText: "",
}};
global.exportResultViewHelpers = {{
  outputDestinationToOpen(options) {{
    return options.exportDestinations[0] || "";
  }},
}};
global.isBridgeBatch = () => true;
global.bridgeErrorMessage = (error) => error.message;
const bridgeCalls = [];
global.bridgeRequest = async (path, options) => {{
  bridgeCalls.push({{ path, body: JSON.parse(options.body), method: options.method }});
  return {{ ok: true, path: JSON.parse(options.body).path }};
}};
let renders = 0;
global.render = () => {{ renders += 1; }};
global.window = {{
  open() {{
    throw new Error("file fallback should not be used for bridge batches");
  }},
}};
global.formatterHelpers = {{
  pathToFileUrl(path) {{ return `file:///${{path}}`; }},
}};

vm.runInThisContext(fs.readFileSync({json.dumps(str(HELPER_PATH))}, "utf8"));

(async () => {{
  browseOutputs();
  await openOutputFolder({{ dataset: {{ outputFolder: "D:/Archive/Baja" }} }});
  await revealOutputFile({{ dataset: {{ outputPath: "D:/Archive/Baja/a_BAJA.jpg" }} }});

  assert.equal(state.outputBrowserOpen, true);
  assert.deepEqual(bridgeCalls, [
    {{ path: "/folders/open", method: "POST", body: {{ path: "D:/Archive/Baja" }} }},
    {{ path: "/files/reveal", method: "POST", body: {{ path: "D:/Archive/Baja/a_BAJA.jpg" }} }},
  ]);
  assert.equal(state.statusText, "Archivo de salida localizado");
  assert.equal(renders, 3);
}})().catch((error) => {{
  console.error(error);
  process.exitCode = 1;
}});
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend action checks")
def test_browse_outputs_opens_result_panel_and_scrolls_it_into_view():
    script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const scrollCalls = [];
global.state = {{
  inspectorTab: "review",
  outputBrowserOpen: false,
  statusText: "",
}};
global.document = {{
  querySelector(selector) {{
    assert.equal(selector, "#export-result");
    return {{ scrollIntoView(options) {{ scrollCalls.push(options); }} }};
  }},
}};
let renders = 0;
global.render = () => {{ renders += 1; }};
global.exportResultViewHelpers = {{}};
global.isBridgeBatch = () => true;
global.formatterHelpers = {{ pathToFileUrl(path) {{ return `file:///${{path}}`; }} }};

vm.runInThisContext(fs.readFileSync({json.dumps(str(HELPER_PATH))}, "utf8"));

browseOutputs();

assert.equal(state.inspectorTab, "output");
assert.equal(state.outputBrowserOpen, true);
assert.equal(state.statusText, "Salidas exportadas");
assert.equal(renders, 1);
assert.deepEqual(scrollCalls, [{{ block: "start", behavior: "smooth" }}]);

browseOutputs();

assert.equal(state.inspectorTab, "review");
assert.equal(state.outputBrowserOpen, false);
assert.equal(state.statusText, "Resultado de exportación");
assert.equal(renders, 2);
assert.deepEqual(scrollCalls, [{{ block: "start", behavior: "smooth" }}]);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
