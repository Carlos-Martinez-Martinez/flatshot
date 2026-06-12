import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import audit_css  # noqa: E402


def test_frontend_loads_only_modular_css_in_contract_order():
    links = audit_css.linked_stylesheets(FRONTEND_DIR / "index.html")

    assert links == audit_css.CSS_MODULE_ORDER
    assert not ({Path(link).name for link in links} & audit_css.LEGACY_STYLESHEETS)
    assert all((FRONTEND_DIR / link).exists() for link in links)
    assert len(links) == 43
    for legacy_stylesheet in audit_css.LEGACY_STYLESHEETS:
        assert not (FRONTEND_DIR / legacy_stylesheet).exists()


def test_frontend_assets_share_css_module_cache_token():
    assert audit_css.stylesheet_versions(FRONTEND_DIR / "index.html") == {"20260611-css-modules"}


def test_css_modules_keep_cascade_contract():
    paths = audit_css.active_css_paths(FRONTEND_DIR)
    metrics = audit_css.css_metrics(paths)

    assert metrics["total_lines"] <= 9_000
    assert metrics["total_important"] <= 25
    assert metrics["legacy_state_class_selectors"] == 0
    assert metrics["duplicated_selectors_same_context"] == {}
    assert metrics["duplicated_selector_groups_same_context"] == {}
    assert max(item["lines"] for item in metrics["files"]) <= 500
    assert audit_css.legacy_compat_payload(FRONTEND_DIR / "css" / "99-legacy-compat.css") == ""
    for path in paths:
        if path.name == "99-legacy-compat.css":
            continue
        layer, payload = audit_css.css_layer_payload(path)
        assert layer == audit_css.CSS_LAYER_NAME
        assert "{" in payload, f"{path} is linked but has no active rules"


def test_frontend_does_not_apply_runtime_design_system_classes():
    app_js = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")

    assert "renderDesignSystemComponents" not in app_js
    assert "addComponentClass" not in app_js
    assert "ui-button" not in app_js
    assert "ui-summary-card" not in app_js


def test_frontend_css_uses_data_state_contract_instead_of_legacy_shell_classes():
    legacy_state_classes = (
        "no-batch",
        "empty-batch",
        "has-batch",
        "has-status-footer",
        "is-exporting",
        "is-scanning",
        "is-output-editing",
    )
    frontend_sources = [FRONTEND_DIR / "app.js", *audit_css.active_css_paths(FRONTEND_DIR)]

    for path in frontend_sources:
        text = path.read_text(encoding="utf-8")
        for class_name in legacy_state_classes:
            assert class_name not in text, f"{class_name} returned in {path}"


def test_root_tokens_are_owned_by_tokens_module():
    paths = audit_css.active_css_paths(FRONTEND_DIR)
    metrics = audit_css.css_metrics(paths)
    root_owners = {
        item["name"]: item["root_blocks"]
        for item in metrics["files"]
        if item["root_blocks"]
    }

    assert root_owners == {"css/00-settings/tokens.css": 7}
    assert metrics["duplicated_tokens_across_files"] == {}


def test_css_audit_check_mode_passes_current_contract():
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "audit_css.py"), "--check"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
