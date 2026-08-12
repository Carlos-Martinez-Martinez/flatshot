import subprocess
import sys
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import audit_css  # noqa: E402


def css_token_value(source: str, token: str) -> str:
    match = re.search(rf"{re.escape(token)}:\s*([^;]+);", source)
    assert match, f"{token} not found"
    return match.group(1).strip()


def relative_luminance(hex_color: str) -> float:
    value = hex_color.strip()
    assert re.fullmatch(r"#[0-9a-fA-F]{6}", value), value
    channels = [int(value[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(first: str, second: str) -> float:
    first_luminance = relative_luminance(first)
    second_luminance = relative_luminance(second)
    lighter, darker = sorted([first_luminance, second_luminance], reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def repeated_declaration_blocks(css: str) -> dict[str, list[str]]:
    css_without_comments = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    rule_re = re.compile(r"([^{}@][^{}]*)\{([^{}]*)\}", re.S)
    blocks: dict[str, list[str]] = {}
    for match in rule_re.finditer(css_without_comments):
        selector = " ".join(match.group(1).split())
        declarations = [
            " ".join(declaration.split())
            for declaration in match.group(2).split(";")
            if ":" in declaration
        ]
        if len(declarations) >= 3:
            blocks.setdefault("; ".join(declarations), []).append(selector)

    return {
        declarations: selectors
        for declarations, selectors in blocks.items()
        if len(selectors) > 1
    }


def test_frontend_loads_only_modular_css_in_contract_order():
    links = audit_css.linked_stylesheets(FRONTEND_DIR / "index.html")

    assert links == audit_css.CSS_MODULE_ORDER
    assert not ({Path(link).name for link in links} & audit_css.LEGACY_STYLESHEETS)
    assert all((FRONTEND_DIR / link).exists() for link in links)
    assert len(links) == 44
    for legacy_stylesheet in audit_css.LEGACY_STYLESHEETS:
        assert not (FRONTEND_DIR / legacy_stylesheet).exists()


def test_frontend_assets_share_css_module_cache_token():
    assert audit_css.stylesheet_versions(FRONTEND_DIR / "index.html") == {"20260721-empty-folder-icon"}


def test_css_modules_keep_cascade_contract():
    paths = audit_css.active_css_paths(FRONTEND_DIR)
    metrics = audit_css.css_metrics(paths)

    assert metrics["total_lines"] <= audit_css.CSS_TOTAL_LINE_LIMIT
    assert metrics["total_important"] <= audit_css.CSS_IMPORTANT_LIMIT
    assert metrics["legacy_state_class_selectors"] == 0
    assert metrics["duplicated_selectors_same_context"] == {}
    assert metrics["duplicated_selector_groups_same_context"] == {}
    assert max(item["lines"] for item in metrics["files"]) <= audit_css.CSS_FILE_LINE_LIMIT
    assert audit_css.legacy_compat_payload(FRONTEND_DIR / "css" / "99-legacy-compat.css") == ""
    for path in paths:
        if path.name == "99-legacy-compat.css":
            continue
        layer, payload = audit_css.css_layer_payload(path)
        assert layer == audit_css.CSS_LAYER_NAME
        assert "{" in payload, f"{path} is linked but has no active rules"


def test_css_cascade_inventory_matches_current_runtime_order():
    inventory = (PROJECT_ROOT / "docs" / "CSS_CASCADE_INVENTORY.md").read_text(
        encoding="utf-8"
    )

    assert "`css/06-inspector-export/background-presets.css`" in inventory
    for index, stylesheet in enumerate(audit_css.CSS_MODULE_ORDER, start=1):
        assert f"{index}. `{stylesheet}`" in inventory


def test_css_audit_reports_no_unreferenced_runtime_classes():
    assert audit_css.unreferenced_css_classes(FRONTEND_DIR) == {}


def test_css_audit_reports_no_unreferenced_runtime_ids():
    assert audit_css.unreferenced_css_ids(FRONTEND_DIR) == {}


def test_primary_button_tokens_meet_normal_text_contrast():
    tokens = (FRONTEND_DIR / "css" / "00-settings" / "tokens.css").read_text(encoding="utf-8")
    primary = css_token_value(tokens, "--color-primary")
    inverse_text = css_token_value(tokens, "--color-text-inverse")

    assert contrast_ratio(primary, inverse_text) >= 4.5


def test_warning_tokens_meet_normal_text_contrast_on_soft_background():
    tokens = (FRONTEND_DIR / "css" / "00-settings" / "tokens.css").read_text(encoding="utf-8")
    warning = css_token_value(tokens, "--color-warning")
    warning_soft = css_token_value(tokens, "--color-warning-soft")

    assert contrast_ratio(warning, warning_soft) >= 4.5


def test_css_modules_do_not_hardcode_previous_primary_rgb():
    stale_primary_rgb = re.compile(r"rgba?\(\s*15\s*,\s*143\s*,\s*114\b")
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if stale_primary_rgb.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_surface_tokens_instead_of_hex_white():
    hex_white = re.compile(r"(?i)(?<![\w-])#(?:fff|ffffff)(?![\w-])")
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css" and hex_white.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_semantic_tokens_for_warning_error_surfaces():
    hardcoded_status_colors = re.compile(
        r"(?i)#(?:fffaf0|fff8df|fff7f6|f0d59c|f4b5ae|e2c76f|ead58c|9a5b00)\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and hardcoded_status_colors.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_do_not_use_hex_colors_outside_tokens():
    hex_color = re.compile(r"(?i)(?<![\w-])#[0-9a-f]{3,8}(?![\w-])")
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and hex_color.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_tokens_for_shared_slate_alpha_colors():
    shared_slate_alpha = re.compile(r"rgba\(\s*15\s*,\s*23\s*,\s*42\s*,")
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and shared_slate_alpha.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_tokens_for_translucent_surface_colors():
    translucent_surface = re.compile(r"rgba\(\s*255\s*,\s*255\s*,\s*255\s*,")
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and translucent_surface.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_tokens_for_shared_neutral_checker_alpha_colors():
    shared_neutral_alpha = re.compile(
        r"rgba\(\s*(?:11\s*,\s*23\s*,\s*34|0\s*,\s*0\s*,\s*0|100\s*,\s*116\s*,\s*139)\s*,"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and shared_neutral_alpha.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_do_not_use_rgb_colors_outside_tokens():
    rgb_color = re.compile(r"rgba?\(")
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and rgb_color.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_motion_tokens_for_common_durations():
    common_motion_duration = re.compile(r"\b(?:120|140|160|220|2600|9000)ms\b")
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and common_motion_duration.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_font_size_tokens_for_canonical_text_sizes():
    canonical_font_size = re.compile(r"\bfont-size\s*:\s*(?:10|11|12|13|14|16|18|22)px\b")
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and canonical_font_size.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_font_weight_tokens():
    literal_font_weight = re.compile(
        r"\bfont-weight\s*:\s*(?:normal|bold|[1-9]00|[1-9][0-9]{2})\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and literal_font_weight.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_line_height_and_letter_spacing_tokens():
    literal_text_metrics = re.compile(
        r"\bline-height\s*:\s*(?:1(?:\.\d+)?|20px)\b"
        r"|\bletter-spacing\s*:\s*0\.03em\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and literal_text_metrics.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_radius_tokens_for_canonical_radii():
    canonical_radius = re.compile(
        r"\bborder-radius\s*:\s*(?:4|6|8|10|12|16|999)px\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and canonical_radius.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_radius_tokens_use_canonical_names():
    numeric_radius_alias = re.compile(r"--radius-(?:6|8|12|16)\b")
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if numeric_radius_alias.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_tokens_do_not_keep_obsolete_size_aliases():
    obsolete_alias = re.compile(
        r"--(?:control-h(?:-compact)?|control-height-sm|space-6|line-tight)\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if obsolete_alias.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_tokens_do_not_keep_transition_shorthand_aliases():
    transition_alias = re.compile(r"--transition-(?:fast|standard)\b")
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if transition_alias.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_control_height_token_for_standard_min_height():
    literal_control_min_height = re.compile(r"\b(?:height|min-height)\s*:\s*36px\b")
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and literal_control_min_height.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_control_tokens_for_compact_30px_controls():
    compact_control_size = re.compile(
        r"\b(?:width|height|min-width|min-height)\s*:\s*30px\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and compact_control_size.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_control_tokens_for_smaller_compact_heights():
    compact_control_height = re.compile(
        r"\b(?:height|min-height)\s*:\s*(?:22|24|28)px\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and compact_control_height.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_control_tokens_for_medium_compact_dimensions():
    medium_compact_dimension = re.compile(
        r"\b(?:width|height|min-width|min-height)\s*:\s*34px\b"
        r"|\bgrid-template-columns\s*:\s*auto\s+34px\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and medium_compact_dimension.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_tokens_for_compact_control_slots():
    compact_control_slot = re.compile(
        r"\b(?:width|height|min-width|min-height)\s*:\s*(?:32|38)px\b"
        r"|\bgrid-template-columns\s*:[^;]*(?:26px\s+minmax\(0,\s*1fr\)\s+38px|minmax\(0,\s*1fr\)\s+38px)\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and compact_control_slot.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_output_profile_switch_uses_geometry_tokens():
    css = (FRONTEND_DIR / "css" / "06-inspector-export" / "output-profiles.css").read_text(
        encoding="utf-8"
    )
    switch_literals = re.compile(
        r"\.switch-track\b[^{}]*\{[^{}]*(?:height:\s*20px|width:\s*34px|min-width:\s*34px)"
        r"|\.switch-track::after\b[^{}]*\{[^{}]*(?:width:\s*14px|height:\s*14px|margin:\s*2px)"
        r"|input:checked\s*\+\s*\.switch-track::after\b[^{}]*\{[^{}]*translateX\(14px\)"
    )

    assert not switch_literals.search(css)


def test_slider_thumb_and_selected_guide_swatch_use_size_tokens():
    component_size_literals = re.compile(
        r"input\[type=\"range\"\]::-(?:webkit-slider|moz-range)-thumb\b[^{}]*\{[^{}]*"
        r"\b(?:width|height)\s*:\s*14px\b"
        r"|\.guide-system-row\s+\.viewer-guide-system-swatch\b[^{}]*\{[^{}]*"
        r"\b(?:width|height)\s*:\s*14px\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and component_size_literals.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_gallery_state_markers_use_size_tokens():
    gallery_state_marker_literals = re.compile(
        r"\.image-item\s+\.state-chip\b[^{}]*\{[^{}]*\bmin-height\s*:\s*20px\b"
        r"|\.gallery-column(?:\[[^\]]+\])?\s+\.asset-state\b[^{}]*\{[^{}]*"
        r"\b(?:width|min-width|height|min-height)\s*:\s*20px\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and gallery_state_marker_literals.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_empty_folder_icon_tab_keeps_geometry_local():
    css = (FRONTEND_DIR / "css" / "03-components" / "primitives.css").read_text(
        encoding="utf-8"
    )

    assert "var(--empty-icon-" not in css


def test_viewer_guides_count_keeps_width_local():
    css = (FRONTEND_DIR / "css" / "05-viewer" / "viewer-toolbar.css").read_text(
        encoding="utf-8"
    )

    assert "--viewer-guides-count-min-width" not in css


def test_compact_indicators_use_size_tokens():
    compact_indicator_literals = re.compile(
        r"\.bridge-message\b[^{}]*\{[^{}]*\bmin-height\s*:\s*18px\b"
        r"|\.batch-rail\s+\.batch-filter\s+button\s+span\b[^{}]*\{[^{}]*"
        r"\bmin-width\s*:\s*18px\b"
        r"|\.gallery-toolbar__summary\b[^{}]*\{[^{}]*\bmin-height\s*:\s*18px\b"
        r"|\.preflight-item\s*>\s*span\b[^{}]*\{[^{}]*"
        r"\b(?:width|height)\s*:\s*18px\b"
        r"|\.lighting-stage__handle\b[^{}]*\{[^{}]*\b(?:width|height)\s*:\s*18px\b"
        r"|\.output-toggle\s+input\b[^{}]*\{[^{}]*\b(?:width|height)\s*:\s*18px\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and compact_indicator_literals.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_folder_empty_icon_override_does_not_duplicate_hidden_tab_geometry():
    css = (FRONTEND_DIR / "css" / "03-components" / "empty-states.css").read_text(
        encoding="utf-8"
    )
    match = re.search(
        r"\.empty-state:is\(\.onboarding, \.batch-empty\)\s+\.empty-icon::before\s*\{([^{}]*)\}",
        css,
    )
    assert match, "shared folder empty icon override not found"

    rule = match.group(1)
    assert "content: none" in rule
    assert not re.search(r"\b(?:left|top|width|height|border|border-radius|background)\s*:", rule)


def test_gallery_thumbnail_dimensions_use_tokens():
    thumbnail_dimension_literals = re.compile(
        r"\.thumb\b[^{}]*\{[^{}]*\b(?:width|height)\s*:\s*56px\b"
        r"|\.batch-rail\s+\.thumb\b[^{}]*\{[^{}]*\b(?:width|height)\s*:\s*48px\b"
        r"|\.gallery-column\[data-gallery-view=\"list\"\]\s+\.thumb\b[^{}]*\{[^{}]*"
        r"\b(?:width|height)\s*:\s*52px\b"
        r"|\.gallery-column\[data-gallery-view=\"list\"\]\s+\.thumb-image\b[^{}]*\{[^{}]*"
        r"\b(?:width|height|max-width|max-height)\s*:\s*40px\b"
        r"|\.batch-panel\s+\.image-item\b[^{}]*\{[^{}]*"
        r"\bgrid-template-columns\s*:\s*56px\b"
        r"|\.gallery-column\[data-gallery-view=\"list\"\]\s+\.image-item\b[^{}]*\{[^{}]*"
        r"\bgrid-template-columns\s*:\s*56px\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and thumbnail_dimension_literals.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_batch_rail_asset_rows_do_not_use_overfit_metric_tokens():
    css = (FRONTEND_DIR / "css" / "04-batch-gallery" / "batch-rail.css").read_text(
        encoding="utf-8"
    )

    assert "--batch-rail-row-min-height" not in css
    assert "--batch-rail-thumb-column" not in css


def test_hidden_gallery_active_marker_does_not_keep_geometry():
    css = (FRONTEND_DIR / "css" / "04-batch-gallery" / "image-grid.css").read_text(
        encoding="utf-8"
    )
    hidden_active_marker_geometry = re.compile(
        r"\.gallery-column\[data-gallery-view=\"list\"\]\s+\.image-item\.active::after\s*\{"
        r"[^{}]*(?:left|top|max-width|overflow|text-overflow)\s*:"
        r"|\.gallery-column\s+\.image-item\.active::after\s*\{[^{}]*"
        r"(?:position|left|top|z-index|border-radius|background|padding|color|font-size|font-weight|line-height)\s*:"
    )

    assert not hidden_active_marker_geometry.search(css)


def test_gallery_card_layout_metrics_do_not_use_overfit_tokens():
    css = (FRONTEND_DIR / "css" / "04-batch-gallery" / "image-grid.css").read_text(
        encoding="utf-8"
    )
    overfit_tokens = [
        "--gallery-card-preview-row",
        "--batch-image-row-min-height",
        "--gallery-list-thumb-column",
        "--image-status-label-max-width",
        "--gallery-list-row-min-height",
        "--gallery-card-min-height",
        "--gallery-thumb-card-min-height",
        "--gallery-thumb-copy-min-height",
    ]

    for token in overfit_tokens:
        assert token not in css


def test_inspector_control_rows_keep_grid_metrics_local():
    overfit_grid_tokens = re.compile(
        r"--(?:control-row-label-min|control-row-input-min|"
        r"control-row-value-width|local-control-row-label-min)\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and overfit_grid_tokens.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_topbar_heights_use_shared_token_without_local_height_aliases():
    component_height_literals = re.compile(
        r"\.top-export\b[^{}]*\{[^{}]*\bmin-height\s*:\s*42px\b"
        r"|\.top-action-cluster\b[^{}]*\{[^{}]*\bmin-height\s*:\s*42px\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and component_height_literals.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_component_specific_48px_metrics_do_not_use_unnecessary_aliases():
    component_metric_literals = re.compile(
        r"\.lighting-stage__product\b[^{}]*\{[^{}]*\bheight\s*:\s*48px\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and component_metric_literals.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_component_specific_58px_metrics_do_not_use_unnecessary_aliases():
    css = (FRONTEND_DIR / "css" / "03-components" / "forms.css").read_text(
        encoding="utf-8"
    )

    assert "--viewer-status-label-min-width" not in css


def test_component_specific_action_metrics_use_control_height_directly():
    overfit_action_tokens = re.compile(
        r"--(?:recent-folder-action-size|viewer-guides-toggle-size|"
        r"guide-system-controls-offset|rgb-swatch-width|active-output-edit-size)\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and overfit_action_tokens.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_guide_manager_layout_keeps_local_grid_metrics_local():
    css = (FRONTEND_DIR / "css" / "05-viewer" / "viewer-toolbar.css").read_text(
        encoding="utf-8"
    )
    overfit_tokens = [
        "--guide-manager-body-grid",
        "--guide-system-row-min-height",
        "--guide-system-main-grid",
        "--guide-empty-state-min-height",
        "--guide-draft-fields-grid",
        "--guide-draft-fields-compact-grid",
        "--guide-readonly-fields-grid",
        "--guide-add-row-grid",
        "--guide-add-row-compact-grid",
        "--guide-list-heading-min-height",
        "--guide-line-row-grid",
        "--guide-line-row-min-height",
        "--guide-line-readonly-grid",
        "--guide-readonly-row-min-height",
        "--guide-manager-actions-min-height",
        "--guide-system-list-compact-max-height",
        "--guide-system-list-card-grid",
    ]

    for token in overfit_tokens:
        assert token not in css


def test_footer_layout_keeps_local_progress_metrics_local_and_no_dead_overrides():
    css = (FRONTEND_DIR / "css" / "02-layout" / "footer.css").read_text(
        encoding="utf-8"
    )

    assert "min-height: 26px" not in css
    assert "padding-block: 2px" not in css
    assert "grid-template-columns: minmax(0, 1fr) auto" not in css
    assert ".bottom-actions .primary {\n  display: none;\n}" not in css

    assert "--footer-progress-export-width" not in css
    assert "--footer-progress-min-width" not in css
    assert "--footer-progress-meter-width" not in css
    assert "min-height: var(--control-height)" in css


def test_button_base_uses_shared_icon_token_without_width_aliases():
    css = (FRONTEND_DIR / "css" / "03-components" / "buttons.css").read_text(
        encoding="utf-8"
    )

    icon_metric_literals = [
        r"\.button-icon\b[^{}]*\{[^{}]*(?:width|height)\s*:\s*16px\b",
        r"\.button-icon\s+svg\b[^{}]*\{[^{}]*(?:width|height)\s*:\s*16px\b",
    ]

    for pattern in icon_metric_literals:
        assert not re.search(pattern, css), pattern

    assert "--button-primary-min-width" not in css
    assert "--button-onboarding-primary-min-width" not in css
    assert "width: var(--button-icon-size)" in css
    assert "height: var(--button-icon-size)" in css


def test_control_track_heights_use_shared_token():
    form_css = (FRONTEND_DIR / "css" / "03-components" / "forms.css").read_text(
        encoding="utf-8"
    )
    progress_css = (
        FRONTEND_DIR / "css" / "03-components" / "progress-loaders.css"
    ).read_text(encoding="utf-8")

    assert "height: 6px" not in form_css
    assert "height: 6px" not in progress_css
    assert "height: var(--control-track-height)" in form_css
    assert "height: var(--control-track-height)" in progress_css


def test_form_control_local_metrics_do_not_use_overfit_tokens():
    css = (FRONTEND_DIR / "css" / "03-components" / "forms.css").read_text(
        encoding="utf-8"
    )

    assert "--range-thumb-offset-y" not in css
    assert "--zoom-label-min-width" not in css
    assert "width: var(--control-size-2xs)" in css


def test_recent_spacing_cleanup_uses_existing_scale_tokens():
    tokens_css = (
        FRONTEND_DIR / "css" / "00-settings" / "tokens.css"
    ).read_text(encoding="utf-8")
    overfit_tokens = [
        "--space-1-25",
        "--compact-card-padding",
        "--gallery-section-offset",
    ]

    for token in overfit_tokens:
        assert token not in tokens_css


def test_compact_card_padding_uses_existing_scale_tokens():
    compact_padding = re.compile(r"\bpadding\s*:\s*9px\s+10px\b")
    compact_padding_token = re.compile(r"\bpadding\s*:\s*var\(--compact-card-padding\)")
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and (
            compact_padding.search(path.read_text(encoding="utf-8"))
            or compact_padding_token.search(path.read_text(encoding="utf-8"))
        )
    ]

    assert offenders == []


def test_workflow_inline_width_uses_token():
    inline_width = re.compile(r"\bwidth\s*:\s*min\(640px,\s*100%\)")
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and inline_width.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_micro_gap_uses_existing_spacing_token():
    micro_gap = re.compile(r"\bgap\s*:\s*5px\b")
    micro_gap_token = re.compile(r"\bgap\s*:\s*var\(--space-1-25\)")
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and (
            micro_gap.search(path.read_text(encoding="utf-8"))
            or micro_gap_token.search(path.read_text(encoding="utf-8"))
        )
    ]

    assert offenders == []


def test_gallery_section_offsets_use_existing_spacing_token():
    gallery_section_offset = re.compile(r"\bmargin-top\s*:\s*10px\b")
    gallery_section_offset_token = re.compile(
        r"\bmargin-top\s*:\s*var\(--gallery-section-offset\)"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and (
            gallery_section_offset.search(path.read_text(encoding="utf-8"))
            or gallery_section_offset_token.search(path.read_text(encoding="utf-8"))
        )
    ]

    assert offenders == []


def test_css_modules_use_popover_gutter_token_for_compact_viewport_offsets():
    compact_viewport_gutter = re.compile(r"\bcalc\(100vw\s*-\s*32px\)")
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and compact_viewport_gutter.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_modal_gutter_token_for_viewport_offsets():
    viewport_gutter = re.compile(r"\bcalc\((?:100vw|100vh|100%)\s*-\s*48px\)")
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and viewport_gutter.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_spacing_tokens_for_standard_spacing_values():
    spacing_declaration = re.compile(
        r"\b(?:gap|row-gap|column-gap|padding(?:-(?:block|inline|top|right|bottom|left))?|"
        r"margin(?:-(?:block|inline|top|right|bottom|left))?)\s*:[^;]*"
        r"(?<![\w-])(?:4|8|12|16|24|32)px(?![\w-])"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and spacing_declaration.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_spacing_tokens_for_compact_gap_values():
    compact_gap = re.compile(
        r"\b(?:gap|row-gap|column-gap)\s*:[^;]*(?<![\w-])(?:2|3|6|10)px(?![\w-])"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and compact_gap.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_border_width_tokens_for_hairline_borders():
    hairline_border = re.compile(
        r"\bborder(?:-(?:top|right|bottom|left|inline|block|inline-start|inline-end|"
        r"block-start|block-end))?\s*:\s*1px\b|\bborder-width\s*:\s*1px\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and hairline_border.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_border_width_tokens_for_strong_borders():
    strong_border = re.compile(
        r"\bborder(?:-(?:top|right|bottom|left|inline|block|inline-start|inline-end|"
        r"block-start|block-end))?\s*:\s*2px\b|\bborder-width\s*:\s*2px\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and strong_border.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_border_width_token_for_hairline_shadow_rings():
    hairline_shadow_ring = re.compile(
        r"\bbox-shadow\s*:[^;]*(?:inset\s+)?0\s+0\s+0\s+1px\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and hairline_shadow_ring.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_border_width_token_for_strong_shadow_rings():
    strong_shadow_ring = re.compile(
        r"\bbox-shadow\s*:[^;]*(?:inset\s+)?0\s+0\s+0\s+2px\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and strong_shadow_ring.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_border_width_token_for_emphasis_strokes():
    emphasis_stroke = re.compile(
        r"\bborder(?:-(?:top|right|bottom|left|inline|block|inline-start|inline-end|"
        r"block-start|block-end))?\s*:\s*3px\b"
        r"|\bbox-shadow\s*:[^;]*(?:inset\s+3px\s+0\s+0|0\s+0\s+0\s+3px)\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and emphasis_stroke.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_tokens_for_focus_outline_geometry():
    focus_outline_geometry = re.compile(
        r"\boutline\s*:\s*2px\b|\boutline-offset\s*:\s*2px\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and focus_outline_geometry.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_do_not_use_shadow_tokens_as_outline_colors():
    invalid_outline_color = re.compile(r"\boutline\s*:[^;]*var\(--focus-ring\)")
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and invalid_outline_color.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_states_module_supports_forced_colors_focus_and_borders():
    css = (FRONTEND_DIR / "css" / "08-states-responsive" / "states.css").read_text(
        encoding="utf-8"
    )

    assert "@media (forced-colors: active)" in css
    assert "outline-color: Highlight;" in css
    assert "border-color: CanvasText;" in css


def test_css_modules_use_icon_stroke_width_token():
    icon_stroke_width = re.compile(r"\bstroke-width\s*:\s*2\b")
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and icon_stroke_width.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_tokens_for_small_status_indicators():
    small_indicator_size = re.compile(r"\b(?:width|height)\s*:\s*(?:7|9)px\b")
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and small_indicator_size.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_css_modules_use_semantic_token_for_visually_hidden_size():
    visually_hidden_size = re.compile(r"\b(?:width|height)\s*:\s*1px\b")
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and visually_hidden_size.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_high_churn_inspector_modules_do_not_repeat_declaration_blocks():
    offenders = {}
    for relative_path in [
        "css/06-inspector-export/inspector-cards.css",
        "css/06-inspector-export/inspector-shell.css",
    ]:
        css = (FRONTEND_DIR / relative_path).read_text(encoding="utf-8")
        repeated = repeated_declaration_blocks(css)
        if repeated:
            offenders[relative_path] = repeated

    assert offenders == {}


def test_css_modules_use_checker_tokens_for_checkerboard_geometry():
    checker_geometry = re.compile(
        r"\bbackground-size\s*:\s*(?:8|12|14|16|24)px\s+(?:8|12|14|16|24)px\b"
        r"|\bbackground-position\s*:\s*0 0,\s*0 (?:4|6|7|8|12)px,\s*"
        r"(?:4|6|7|8|12)px -(?:4|6|7|8|12)px,\s*-(?:4|6|7|8|12)px 0\b"
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "tokens.css"
        and checker_geometry.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_hidden_attribute_display_rule_is_owned_by_base_module():
    hidden_display_rule = re.compile(
        r"[^{}]*(?<!:not\()\[[^\]]*\bhidden\b[^\]]*\][^{}]*\{[^{}]*\bdisplay\s*:",
        re.DOTALL,
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "base.css"
        and hidden_display_rule.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_is_hidden_display_rule_is_owned_by_states_module():
    is_hidden_display_rule = re.compile(
        r"[^{}]*(?<!:not\()\.[A-Za-z0-9_-]*is-hidden[^{}]*\{[^{}]*\bdisplay\s*:",
        re.DOTALL,
    )
    offenders = [
        path.relative_to(FRONTEND_DIR).as_posix()
        for path in audit_css.active_css_paths(FRONTEND_DIR)
        if path.name != "states.css"
        and is_hidden_display_rule.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_declared_css_tokens_are_reachable_from_active_frontend():
    tokens_css = FRONTEND_DIR / "css" / "00-settings" / "tokens.css"
    token_source = tokens_css.read_text(encoding="utf-8")
    token_values = {}
    for match in re.finditer(r"--([A-Za-z0-9_-]+)\s*:\s*([^;]+);", token_source):
        token_values.setdefault(match.group(1), []).append(match.group(2))

    reachable = set()
    for path in list(audit_css.active_css_paths(FRONTEND_DIR)) + [
        path
        for path in FRONTEND_DIR.rglob("*")
        if path.is_file() and path.suffix in {".html", ".js"}
    ]:
        source = path.read_text(encoding="utf-8")
        if path == tokens_css:
            source = re.sub(r"--[A-Za-z0-9_-]+\s*:", "", source)
        reachable.update(re.findall(r"--([A-Za-z0-9_-]+)\b", source))

    pending = list(reachable)
    while pending:
        name = pending.pop()
        for value in token_values.get(name, []):
            for dependency in re.findall(r"--([A-Za-z0-9_-]+)\b", value):
                if dependency not in reachable:
                    reachable.add(dependency)
                    pending.append(dependency)

    assert sorted(set(token_values) - reachable) == []


def test_modal_layout_dimensions_use_semantic_tokens():
    batch_detail_css = (
        FRONTEND_DIR / "css" / "07-modals" / "batch-detail.css"
    ).read_text(encoding="utf-8")
    viewer_toolbar_css = (
        FRONTEND_DIR / "css" / "05-viewer" / "viewer-toolbar.css"
    ).read_text(encoding="utf-8")

    assert "min(900px" not in batch_detail_css
    assert "calc(100vw - 48px)" not in batch_detail_css
    assert "calc(100vh - 48px)" not in batch_detail_css
    assert "min(1280px" not in viewer_toolbar_css
    assert "calc(100vw - 72px)" not in viewer_toolbar_css
    assert "calc(100vh - 72px)" not in viewer_toolbar_css
    assert "padding: 36px" not in viewer_toolbar_css


def test_responsive_module_consolidates_adjacent_media_blocks():
    responsive_css = (
        FRONTEND_DIR / "css" / "08-states-responsive" / "responsive.css"
    ).read_text(encoding="utf-8")
    media_queries = re.findall(r"@media\s*\(([^)]+)\)\s*{", responsive_css)

    assert media_queries == [
        "min-width: 1600px",
        "max-width: 1599px",
        "max-width: 1240px",
        "max-width: 1119px",
        "max-width: 759px",
    ]
    assert all(
        current != following
        for current, following in zip(media_queries, media_queries[1:], strict=False)
    )


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


def test_css_audit_detects_multiline_duplicate_selector_groups(tmp_path):
    first = tmp_path / "first.css"
    second = tmp_path / "second.css"
    first.write_text(
        """
@layer flatshot {
.alpha,
.beta {
  color: red;
}

@media (max-width: 720px) {
  .alpha,
  .beta {
    color: blue;
  }
}
}
""",
        encoding="utf-8",
    )
    second.write_text(
        """
@layer flatshot {
.beta,
.alpha {
  color: green;
}
}
""",
        encoding="utf-8",
    )

    groups = audit_css.duplicated_selector_groups_same_context([first, second])

    assert set(groups) == {"root :: .alpha, .beta"}
    assert groups["root :: .alpha, .beta"]["count"] == 2


def test_root_tokens_are_owned_by_tokens_module():
    paths = audit_css.active_css_paths(FRONTEND_DIR)
    metrics = audit_css.css_metrics(paths)
    root_owners = {
        item["name"]: item["root_blocks"]
        for item in metrics["files"]
        if item["root_blocks"]
    }

    assert root_owners == {"css/00-settings/tokens.css": 5}
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


def test_css_line_budget_allows_moderate_growth_without_disabling_structure_checks():
    payload = audit_css.build_payload(PROJECT_ROOT)
    payload["metrics"] = dict(payload["metrics"])
    payload["metrics"]["total_lines"] = 10_500

    failures = audit_css.css_contract_failures(PROJECT_ROOT, payload)

    assert not any("CSS line count exceeds" in failure for failure in failures)


def test_css_file_line_budget_allows_moderate_module_growth():
    payload = audit_css.build_payload(PROJECT_ROOT)
    metrics = dict(payload["metrics"])
    files = [dict(item) for item in metrics["files"]]
    files[0]["lines"] = 625
    metrics["files"] = files
    payload["metrics"] = metrics

    failures = audit_css.css_contract_failures(PROJECT_ROOT, payload)

    assert not any("CSS modules exceed" in failure for failure in failures)


def test_advanced_disclosures_keep_content_sized_rows():
    css = (
        FRONTEND_DIR
        / "css"
        / "06-inspector-export"
        / "advanced-local-overrides.css"
    ).read_text(encoding="utf-8")

    assert "overflow-y: auto" in css
    assert "flex: 1 1 auto" not in css
    assert "height: 100%" not in css


def test_active_output_row_main_keeps_grid_layout_when_selectable():
    buttons_css = (
        FRONTEND_DIR
        / "css"
        / "03-components"
        / "buttons.css"
    ).read_text(encoding="utf-8")
    output_profiles_css = (
        FRONTEND_DIR
        / "css"
        / "06-inspector-export"
        / "output-profiles.css"
    ).read_text(encoding="utf-8")

    assert "button:where([data-action]" in buttons_css
    assert ":where(:not(.primary):not(.active)" in buttons_css
    assert ":not(.active-output-row__main)" not in buttons_css
    assert "button.active-output-row__main {\n  cursor: pointer;" in output_profiles_css
    assert ".active-output-row__main {\n  min-width: 0;\n  width: 100%;\n  display: grid;" in output_profiles_css
    assert "justify-content: stretch;" in output_profiles_css
    assert "justify-items: start;" in output_profiles_css
    assert "border: 0;\n  background: transparent;" in output_profiles_css
    assert "font-weight: var(--font-weight-regular);" in output_profiles_css
    assert ".active-output-row__main small {\n  overflow: visible;" in output_profiles_css
    assert "button.active-output-row__main:focus-visible {" not in output_profiles_css
    assert ".active-output-row:has(.active-output-row__main:focus-visible) {" in output_profiles_css
    focus_rule = output_profiles_css.split(".active-output-row:has(.active-output-row__main:focus-visible) {", 1)[1].split("}", 1)[0]
    assert "box-shadow: var(--shadow-focus)" in focus_rule
    assert (
        ".active-output-row.is-current {\n"
        "  border-color: color-mix(in srgb, var(--semantic-selection-border) 42%, var(--color-border));"
        in output_profiles_css
    )
    assert (
        "background: color-mix(in srgb, var(--semantic-selection-soft) 24%, var(--color-bg-panel));"
        in output_profiles_css
    )
    assert "inset var(--border-width-emphasis) 0 0 var(--semantic-selection)" not in output_profiles_css
    assert ".active-output-row__preview-badge {" not in output_profiles_css


def test_button_defaults_avoid_long_negative_selector_lists():
    css = (
        FRONTEND_DIR
        / "css"
        / "03-components"
        / "buttons.css"
    ).read_text(encoding="utf-8")

    assert "button:not(.image-item):not(.preset-chip)" not in css
    assert "button:not(.primary):not(.active)" not in css
    assert "[data-action]" in css
