import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "empty-state-view.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_empty_state_view_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("empty-state-view.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_empty_state_view_keeps_existing_html_contract():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.equal(helpers.escapeHtml("<a&b\\"c>"), "&lt;a&amp;b&quot;c&gt;");

const plain = helpers.emptyStateHtml({{
  title: "Sin lote",
  detail: "Elige <carpeta>",
}});
assert.equal(plain.includes('class="empty-state inline"'), true);
assert.equal(plain.includes('<strong>Sin lote</strong>'), true);
assert.equal(plain.includes('<span>Elige &lt;carpeta&gt;</span>'), true);
assert.equal(plain.includes('<button'), false);
assert.equal(plain.includes('<small>'), false);

const withAction = helpers.emptyStateHtml({{
  variant: 'onboarding "x"',
  title: "Selecciona",
  detail: "Carga",
  actionLabel: "Elegir & abrir",
  action: 'pick-"folder"',
  meta: "PNG & JPG",
}});
assert.equal(withAction.includes('class="empty-state onboarding &quot;x&quot;"'), true);
assert.equal(withAction.includes('data-action="pick-&quot;folder&quot;"'), true);
assert.equal(withAction.includes('>Elegir &amp; abrir</button>'), true);
assert.equal(withAction.includes('<small>PNG &amp; JPG</small>'), true);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
