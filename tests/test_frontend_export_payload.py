import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
OUTPUT_PROFILES_PATH = FRONTEND_DIR / "output-profiles.js"
HELPER_PATH = FRONTEND_DIR / "export-payload.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_export_payload_helper_loads_after_profiles_and_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    profiles_index = html.index("output-profiles.js")
    payload_index = html.index("export-payload.js")
    app_index = html.index("app.js")

    assert profiles_index < payload_index < app_index


def test_frontend_assets_share_output_flow_cache_token():
    html = INDEX_PATH.read_text(encoding="utf-8")
    asset_versions = re.findall(r'[<](?:script|link)[^>]+[?]v=([^"&]+)', html)

    assert asset_versions
    assert set(asset_versions) == {"20260721-empty-folder-icon"}


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_export_payload_helper_keeps_bridge_json_contract():
    script = f"""
const assert = require("node:assert/strict");
require({json.dumps(str(OUTPUT_PROFILES_PATH))});
const helpers = require({json.dumps(str(HELPER_PATH))});

const images = [
  {{ id: "a", source: "bridge", bridgeImageId: "img_a", path: "C:/lote/a.png" }},
  {{ id: "b", source: "mock", path: "C:/lote/b.png" }},
  {{ id: "c", source: "bridge", path: "" }},
  {{ id: "d", source: "bridge", imageId: "img_d", path: "C:/lote/d.png" }},
  {{ id: "e", source: "bridge", path: "C:/lote/e.png" }},
];
const profiles = [
  {{
    id: "web_rgb230",
    name: "Web gris claro",
    format: "JPG",
    background: "rgb230",
    destinationMode: "source",
    destinationValue: "Salida",
    naming: "{{original}}{{suffix}}",
    suffix: "_PRO",
    width: 1800,
    height: 2400,
    maxFileSizeKb: 140,
  }},
  {{
    id: "web_rgb230",
    name: "PNG transparente",
    format: "PNG",
    background: "transparent",
    destinationMode: "custom",
    destinationValue: "C:/salida",
    naming: "{{folder}}_{{original}}{{suffix}}",
    suffix: "_PNG",
    width: 1000,
    height: 1200,
    maxFileSizeKb: 80,
  }},
];
const settings = {{ opacity: 20, blur: 14 }};
const curveData = {{ xp: [0, 1], fp: [0.9, 1.1], base_fill: 0.5 }};
const imageOverrides = {{ "C:/lote/a.png": {{ opacity: 10 }} }};

assert.deepEqual(helpers.bridgeImagePaths(images), ["C:/lote/e.png"]);
assert.deepEqual(helpers.bridgeImageIds(images), ["img_a", "img_d"]);
assert.deepEqual(helpers.failedBridgeExportImages(images, [
  {{ name: "a.png", path: "C:/lote/a.png", success: false }},
  {{ name: "d.png", path: "C:/lote/d.png", success: true }},
  {{ name: "missing.png", path: "C:/lote/missing.png", success: false }},
  {{ name: "legacy.png", success: false }},
]), [
  {{ id: "a", source: "bridge", bridgeImageId: "img_a", path: "C:/lote/a.png" }},
]);
assert.equal(helpers.primaryOutputProfile(profiles, "missing", profiles[1]), profiles[0]);
assert.equal(helpers.primaryOutputProfile(profiles, "web_rgb230", profiles[1]), profiles[0]);
assert.equal(helpers.primaryOutputProfile([], "missing", profiles[1]), profiles[1]);

const payload = helpers.buildBridgeExportPayload({{
  activeOutputProfileId: "web_rgb230",
  fallbackProfile: profiles[1],
  imageOverrides,
  images,
  presetName: "Luz cenital",
  profiles,
  settings,
  curveData,
}});

assert.deepEqual(payload, {{
  imageIds: ["img_a", "img_d"],
  imagePaths: ["C:/lote/e.png"],
  presetName: "Luz cenital",
  settings,
  curveData,
  imageOverrides,
  export: {{
    format: "JPG",
    size: "1800x2400",
    background: "rgb230",
    destinationMode: "source",
    destinationValue: "Salida",
    outputFolderName: "Salida",
    customOutputPath: "",
    namingTemplate: "{{original}}{{suffix}}",
    suffix: "_PRO",
    variants: [
      {{
        id: "web_rgb230",
        label: "Web gris claro",
        enabled: true,
        format: "JPG",
        transparent_bg: false,
        bg_color: [230, 230, 230],
        suffix: "_PRO",
        naming_template: "{{original}}{{suffix}}",
        output_destination: "subfolder",
        output_folder_name: "Salida",
        custom_output_path: null,
        output_width: 1800,
        output_height: 2400,
        max_file_size_kb: 140,
      }},
      {{
        id: "web_rgb230_2",
        label: "PNG transparente",
        enabled: true,
        format: "PNG",
        transparent_bg: true,
        bg_color: [230, 230, 230],
        suffix: "_PNG",
        naming_template: "{{folder}}_{{original}}{{suffix}}",
        output_destination: "custom",
        output_folder_name: null,
        custom_output_path: "C:/salida",
        output_width: 1000,
        output_height: 1200,
        max_file_size_kb: null,
      }},
    ],
  }},
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
