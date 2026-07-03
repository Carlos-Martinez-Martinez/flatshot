import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend state checks")
def test_export_profile_changes_do_not_override_viewer_background():
    script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const frontend = {json.dumps(str(FRONTEND_DIR))};

global.state = {{
  activeOutputProfileId: "web",
  outputProfiles: [
    {{
      id: "web",
      name: "Web",
      enabled: true,
      format: "JPG",
      width: 1800,
      height: 2400,
      background: "white",
      destinationMode: "source",
      destinationValue: "Salida",
      naming: "{{original}}{{suffix}}",
      suffix: "_PRO",
      maxFileSizeKb: null,
    }},
  ],
  previewBg: "soft-black",
}};
global.outputProfileHelpers = {{
  outputProfileSize(profile) {{
    return `${{profile.width}}x${{profile.height}}`;
  }},
}};
global.isExportReady = () => true;

vm.runInThisContext(fs.readFileSync(path.join(frontend, "app-output-profile-state.js"), "utf8"));

syncOutputProfileState(state.outputProfiles[0]);

assert.equal(state.background, "white");
assert.equal(state.previewBg, "soft-black");
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend state checks")
def test_export_background_select_does_not_override_viewer_background():
    script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const frontend = {json.dumps(str(FRONTEND_DIR))};

global.state = {{
  background: "rgb230",
  previewBg: "soft-black",
  statusText: "",
}};
global.outputProfileHelpers = {{
  normalizeBackgroundValue(value) {{
    return value || "rgb230";
  }},
}};
global.settingsViewHelpers = {{
  backgroundLabel(value) {{
    return value;
  }},
}};
global.persistExportPreferences = () => {{}};
global.selectedImage = () => null;
global.render = () => {{}};

vm.runInThisContext(fs.readFileSync(path.join(frontend, "app-form-events.js"), "utf8"));

handleBackgroundSelectChange({{ target: {{ value: "white" }} }});

assert.equal(state.background, "white");
assert.equal(state.previewBg, "soft-black");
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend state checks")
def test_applying_output_profile_refreshes_bridge_preview_without_changing_viewer_background():
    script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const frontend = {json.dumps(str(FRONTEND_DIR))};

global.window = {{ localStorage: {{}} }};
global.STORAGE_KEYS = {{
  outputProfiles: "profiles",
  activeOutputProfile: "activeProfile",
  activeOutputFormats: "activeFormats",
}};
global.storageHelpers = {{
  writeJson() {{}},
  writeValue() {{}},
}};
global.state = {{
  activeOutputProfileId: "web",
  outputProfiles: [
    {{
      id: "web",
      name: "Percha web",
      enabled: true,
      format: "JPG",
      width: 1800,
      height: 2400,
      background: "rgb230",
      destinationMode: "source",
      destinationValue: "Salida",
      naming: "{{original}}{{suffix}}",
      suffix: "_PRO",
      maxFileSizeKb: null,
    }},
    {{
      id: "zalando",
      name: "Zalando",
      enabled: true,
      format: "JPG",
      width: 1800,
      height: 2400,
      background: "white",
      destinationMode: "source",
      destinationValue: "Salida",
      naming: "{{original}}{{suffix}}",
      suffix: "_ZAL",
      maxFileSizeKb: null,
    }},
  ],
  outputProfileDraft: null,
  previewBg: "soft-black",
  statusText: "",
}};
global.outputProfileHelpers = {{
  outputProfileSize(profile) {{
    return `${{profile.width}}x${{profile.height}}`;
  }},
}};
global.isExportReady = () => true;
global.persistExportPreferences = () => {{}};
global.scheduleBridgeUiPreferencesSave = () => {{}};
global.render = () => {{}};
const bridgeImage = {{ id: "image-1", source: "bridge", path: "C:/batch/Capa 1.png" }};
const previewRequests = [];
global.selectedImage = () => bridgeImage;
global.requestBridgePreview = (image) => {{
  previewRequests.push({{
    image,
    background: state.background,
    previewBg: state.previewBg,
  }});
  return Promise.resolve();
}};

vm.runInThisContext(fs.readFileSync(path.join(frontend, "app-output-profile-state.js"), "utf8"));
vm.runInThisContext(fs.readFileSync(path.join(frontend, "app-output-profile-apply.js"), "utf8"));

assert.equal(applyOutputProfile("zalando"), true);

assert.equal(state.background, "white");
assert.equal(state.previewBg, "soft-black");
assert.equal(previewRequests.length, 1);
assert.equal(previewRequests[0].image, bridgeImage);
assert.equal(previewRequests[0].background, "white");
assert.equal(previewRequests[0].previewBg, "soft-black");
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend state checks")
def test_preview_color_picker_input_updates_viewer_background_state():
    script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const frontend = {json.dumps(str(FRONTEND_DIR))};

global.window = {{}};
global.SOFT_BLACK_PREVIEW_BG = "soft-black";
global.state = {{
  previewBg: "rgb230",
  statusText: "",
}};
global.outputProfileHelpers = require(path.join(frontend, "output-profiles.js"));
global.backgroundPresetHelpers = require(path.join(frontend, "background-presets.js"));
global.numberHelpers = {{
  clampNumber(value, min, max, fallback) {{
    const numeric = Number(value);
    return Number.isFinite(numeric) ? Math.max(min, Math.min(max, numeric)) : fallback;
  }},
}};
global.settingsViewHelpers = {{
  backgroundLabel(value) {{
    return value === "rgb230" ? "gris claro" : value;
  }},
}};

const hiddenValue = {{ value: "rgb:230,230,230" }};
const swatch = {{ style: {{ backgroundColor: "" }} }};
let control;
const picker = {{
  value: "#873636",
  matches(selector) {{
    return selector === "[data-rgb-visual-picker]" || selector === "[data-preview-bg-picker]";
  }},
  closest(selector) {{
    return selector === ".rgb-visual-control" ? control : null;
  }},
}};
control = {{
  dataset: {{
    rgbVisualTarget: "preview-bg-custom-value",
    rgbVisualFormat: "rgb-background",
  }},
  style: {{
    props: {{}},
    setProperty(name, value) {{
      this.props[name] = value;
    }},
  }},
  querySelector(selector) {{
    return selector === "[data-rgb-visual-picker]" ? picker : null;
  }},
  querySelectorAll(selector) {{
    return selector === "[data-rgb-visual-swatch]" ? [swatch] : [];
  }},
}};

global.document = {{
  getElementById(id) {{
    return id === "preview-bg-custom-value" ? hiddenValue : null;
  }},
}};
global.$ = (selector) => {{
  if (selector === "#preview-bg-custom-value") return hiddenValue;
  if (selector === "[data-preview-bg-picker]") return picker;
  if (selector === ".viewer-bg-custom-fields") return control;
  return null;
}};

vm.runInThisContext(fs.readFileSync(path.join(frontend, "app-background-state.js"), "utf8"));
vm.runInThisContext(fs.readFileSync(path.join(frontend, "app-background-preset-controller.js"), "utf8"));

applyPreviewBackgroundPickerChange(picker);

assert.equal(hiddenValue.value, "rgb:135,54,54");
assert.equal(state.previewBg, "rgb:135,54,54");
assert.equal(state.statusText, "Fondo: RGB 135, 54, 54");
assert.equal(control.style.props["--rgb-visual-color"], "rgb(135, 54, 54)");
assert.equal(swatch.style.backgroundColor, "rgb(135, 54, 54)");
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
