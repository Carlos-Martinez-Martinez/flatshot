from __future__ import annotations

import argparse
from pathlib import Path

import e2e_smoke


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"

VISUAL_LANDMARKS = (
    ("app shell", 'class="app-shell'),
    ("top bar", 'class="top-bar"'),
    ("workspace", '<section class="workspace"'),
    ("batch panel", 'class="batch-panel batch-rail"'),
    ("gallery title", 'id="gallery-title"'),
    ("preview panel", 'id="preview-panel"'),
    ("preview canvas", 'id="preview-canvas"'),
    ("settings panel", 'class="settings-panel"'),
    ("preflight chip", 'id="top-preflight-status"'),
    ("export readiness", 'id="export-readiness"'),
    ("top primary action", 'id="top-primary-action"'),
    ("mobile primary action", 'id="primary-action"'),
    ("native module script", 'type="module"'),
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a stdlib visual regression smoke check.")
    parser.add_argument("--frontend-dir", type=Path, default=FRONTEND_DIR)
    args = parser.parse_args(argv)

    with e2e_smoke.serve_frontend(args.frontend_dir) as base_url:
        html = e2e_smoke.fetch_text(f"{base_url}/")
        checked_landmarks = check_visual_landmarks(html)
        e2e_smoke.assert_not_contains(html, 'id="qa-lab-modal"', "QA Lab modal in product HTML")
        checked_assets = e2e_smoke.check_linked_assets(base_url, html)

    print(
        "frontend_visual_regression_smoke OK - "
        f"{checked_landmarks} landmarks, {checked_assets} linked assets"
    )
    return 0


def check_visual_landmarks(html: str) -> int:
    for label, needle in VISUAL_LANDMARKS:
        e2e_smoke.assert_contains(html, needle, label)
    return len(VISUAL_LANDMARKS)


if __name__ == "__main__":
    raise SystemExit(main())
