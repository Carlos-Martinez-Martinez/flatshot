import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "export-history.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_export_history_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("export-history.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_export_history_persists_formats_and_renders_compact_entries():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

function fakeStorage(initial = {{}}, failing = false) {{
  const data = new Map(Object.entries(initial));
  return {{
    getItem(key) {{
      if (failing) throw new Error("blocked");
      return data.has(key) ? data.get(key) : null;
    }},
    setItem(key, value) {{
      if (failing) throw new Error("blocked");
      data.set(key, String(value));
    }},
    dump() {{
      return Object.fromEntries(data.entries());
    }},
  }};
}}

assert.deepEqual(helpers.readExportHistory(fakeStorage({{ history: "{{" }}), "history"), []);
assert.deepEqual(helpers.readExportHistory(fakeStorage({{}}, true), "history"), []);

const storage = fakeStorage();
helpers.rememberExportHistory(storage, "history", {{
  id: "run-1",
  now: "2026-07-03T10:00:00.000Z",
  status: "completed",
  processed: 3,
  total: 3,
  errors: 0,
  destinations: ["C:/Out/A"],
  presetName: "Luz cenital",
  outputProfileName: "JPG gris claro",
  limit: 2,
}});
helpers.rememberExportHistory(storage, "history", {{
  id: "run-2",
  now: "2026-07-03T11:00:00.000Z",
  status: "partial",
  processed: 2,
  total: 3,
  errors: 1,
  destinations: ["C:/Out/B", "C:/Out/C"],
  presetName: "Sin sombra",
  outputProfileName: "PNG transparente",
  limit: 2,
}});
helpers.rememberExportHistory(storage, "history", {{
  id: "run-3",
  now: "2026-07-03T12:00:00.000Z",
  status: "failed",
  processed: 0,
  total: 3,
  errors: 2,
  destinations: ["C:/Out/D"],
  limit: 2,
}});

const entries = helpers.readExportHistory(storage, "history");
assert.deepEqual(entries.map((entry) => entry.id), ["run-3", "run-2"]);
assert.equal(helpers.exportHistoryStatusLabel(entries[0]), "Fallida");
assert.equal(helpers.exportHistoryMeta(entries[1]), "2026-07-03 · 2/3 · 1 error");

const html = helpers.exportHistoryHtml([
  {{
    id: "x",
    status: "completed",
    completedAt: "2026-07-03T12:00:00.000Z",
    processed: 3,
    total: 3,
    errors: 0,
    destinations: ["C:/Out/<A>"],
    presetName: "Luz <cenital>",
    outputProfileName: "JPG",
  }},
]);
assert.equal(html.includes("Historial"), true);
assert.equal(html.includes("Luz &lt;cenital&gt;"), true);
assert.equal(html.includes("C:/Out/&lt;A&gt;"), true);
assert.equal(html.includes("Completada"), true);
assert.equal(helpers.exportHistoryHtml([]), "");

assert.doesNotThrow(() => helpers.rememberExportHistory(fakeStorage({{}}, true), "history", {{ id: "blocked" }}));
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
