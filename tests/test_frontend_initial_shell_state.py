from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend" / "index.html"


def test_static_shell_starts_in_no_folder_state():
    html = INDEX_PATH.read_text(encoding="utf-8")
    main_start = html.index("<main")
    main_tag = html[main_start:html.index(">", main_start)]

    assert 'class="app-shell no-selected-image"' in main_tag
    assert 'data-ui-state="no_folder"' in main_tag
    assert 'data-batch-context="false"' in main_tag
    assert 'data-status-footer="false"' in main_tag
    assert 'data-output-editing="false"' in main_tag
