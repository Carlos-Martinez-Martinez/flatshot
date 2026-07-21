from pathlib import Path


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "apps" / "flatshot-desktop" / "frontend"


def test_source_panel_uses_visible_stable_path_field():
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    source_panel = html.split('<section class="source-panel batch-rail__source"', 1)[1].split("</section>", 1)[0]

    assert "manual-path-panel" not in source_panel
    assert "Ruta manual" not in source_panel
    assert 'class="source-path-panel"' in source_panel
    assert "Carpeta de entrada" in source_panel
    assert 'id="bridge-scan-path"' in source_panel
    assert 'id="bridge-scan-folder"' in source_panel
    assert 'data-action="scan-bridge-folder"' in source_panel


def test_source_path_panel_keeps_stable_layout_styles():
    css = (FRONTEND_DIR / "css" / "04-batch-gallery" / "source-import.css").read_text(encoding="utf-8")

    panel_rule = css.split(".source-path-panel {", 1)[1].split("}", 1)[0]
    input_rule = css.split(".source-path-panel input {", 1)[1].split("}", 1)[0]

    assert "display: grid;" in panel_rule
    assert "grid-template-columns: minmax(0, 1fr) auto;" in panel_rule
    assert "align-items: end;" in panel_rule
    assert "min-width: 0;" in input_rule
    assert "width: 100%;" in input_rule
