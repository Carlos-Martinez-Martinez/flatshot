from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


CSS_MODULE_ORDER = [
    "css/00-settings/tokens.css",
    "css/01-base/base.css",
    "css/02-layout/shell-workspace.css",
    "css/02-layout/topbar.css",
    "css/02-layout/footer.css",
    "css/03-components/primitives.css",
    "css/03-components/workflow-panels.css",
    "css/03-components/review-status-panels.css",
    "css/03-components/buttons.css",
    "css/03-components/forms.css",
    "css/03-components/navigation-controls.css",
    "css/03-components/status-badges.css",
    "css/03-components/cards.css",
    "css/03-components/empty-states.css",
    "css/03-components/progress-loaders.css",
    "css/03-components/dev-debug.css",
    "css/04-batch-gallery/batch-rail.css",
    "css/04-batch-gallery/source-import.css",
    "css/04-batch-gallery/batch-summary.css",
    "css/04-batch-gallery/gallery-shell.css",
    "css/04-batch-gallery/image-grid.css",
    "css/04-batch-gallery/thumbnails.css",
    "css/04-batch-gallery/review-devtools.css",
    "css/05-viewer/viewer-shell.css",
    "css/05-viewer/viewer-toolbar.css",
    "css/05-viewer/canvas.css",
    "css/05-viewer/viewer-states.css",
    "css/06-inspector-export/inspector-shell.css",
    "css/06-inspector-export/inspector-navigation.css",
    "css/06-inspector-export/inspector-workflow.css",
    "css/06-inspector-export/inspector-cards.css",
    "css/06-inspector-export/adjustments-presets.css",
    "css/06-inspector-export/adjustment-controls.css",
    "css/06-inspector-export/advanced-local-overrides.css",
    "css/06-inspector-export/export-panel.css",
    "css/06-inspector-export/output-profiles.css",
    "css/06-inspector-export/background-presets.css",
    "css/06-inspector-export/review-warnings.css",
    "css/07-modals/app-settings.css",
    "css/07-modals/batch-detail.css",
    "css/07-modals/export-confirm.css",
    "css/08-states-responsive/states.css",
    "css/08-states-responsive/responsive.css",
    "css/99-legacy-compat.css",
]

LEGACY_STYLESHEETS = {
    "styles.css",
    "ux-foundation.css",
    "ux-refactor.css",
}

COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)
LINK_RE = re.compile(r"<link\b[^>]*\brel=[\"']stylesheet[\"'][^>]*\bhref=[\"']([^\"']+)[\"']", re.I)
TOKEN_RE = re.compile(r"(?m)^\s*(--[A-Za-z0-9_-]+)\s*:")
ROOT_RE = re.compile(r"(?m)^\s*:root\s*\{")
CLASS_SELECTOR_RE = re.compile(r"\.(-?[_a-zA-Z][_a-zA-Z0-9-]*)")
ID_SELECTOR_RE = re.compile(r"#(-?[_a-zA-Z][_a-zA-Z0-9-]*)")
LEGACY_STATE_CLASS_RE = re.compile(
    r"\.app-shell\.(?:no-batch|empty-batch|has-batch|has-status-footer|is-exporting|is-scanning|is-output-editing)"
)
CSS_LAYER_NAME = "flatshot"
CSS_TOTAL_LINE_LIMIT = 12_000
CSS_IMPORTANT_LIMIT = 10
CSS_FILE_LINE_LIMIT = 650
DYNAMIC_RUNTIME_CLASSES = {
    "bg-custom",
    "bg-rgb230",
    "bg-transparent",
    "bg-white",
    "guide-line--x",
    "guide-line--y",
}
DYNAMIC_RUNTIME_IDS: set[str] = set()


def strip_comments(text: str) -> str:
    return COMMENT_RE.sub("", text)


def normalize_asset_path(href: str) -> str:
    return href.split("?", 1)[0].lstrip("./")


def linked_stylesheets(index_path: Path) -> list[str]:
    html = index_path.read_text(encoding="utf-8")
    return [normalize_asset_path(match) for match in LINK_RE.findall(html)]


def active_css_paths(frontend_dir: Path) -> list[Path]:
    return [frontend_dir / href for href in linked_stylesheets(frontend_dir / "index.html")]


def css_display_name(path: Path) -> str:
    parts = path.parts
    if "css" in parts:
        css_index = parts.index("css")
        return Path(*parts[css_index:]).as_posix()
    return path.name


def stylesheet_versions(index_path: Path) -> set[str]:
    html = index_path.read_text(encoding="utf-8")
    return set(re.findall(r"[<](?:script|link)[^>]+[?]v=([^\"&]+)", html))


def legacy_compat_payload(path: Path) -> str:
    return strip_comments(path.read_text(encoding="utf-8")).strip()


def css_layer_payload(path: Path) -> tuple[str | None, str]:
    text = strip_comments(path.read_text(encoding="utf-8")).strip()
    if not text:
        return None, ""
    prefix = f"@layer {CSS_LAYER_NAME}"
    if not text.startswith(prefix):
        return None, text
    start = text.find("{")
    if start == -1 or not text.endswith("}"):
        return CSS_LAYER_NAME, text
    return CSS_LAYER_NAME, text[start + 1 : -1].strip()


def iter_rule_selectors(paths: list[Path]):
    for path in paths:
        name = css_display_name(path)
        css_without_comments = strip_comments(path.read_text(encoding="utf-8"))
        context_stack: list[str] = []
        pending_selector_lines: list[str] = []
        pending_line_number: int | None = None

        for line_number, raw_line in enumerate(css_without_comments.splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue

            if line == "}":
                pending_selector_lines = []
                pending_line_number = None
                if context_stack:
                    context_stack.pop()
                continue

            if line.endswith("{"):
                prelude = line[:-1].strip()
                selector_start_line = pending_line_number or line_number
                if pending_selector_lines:
                    prelude = " ".join([*pending_selector_lines, prelude])
                    pending_selector_lines = []
                    pending_line_number = None
                prelude = " ".join(prelude.split())

                if prelude.startswith("@"):
                    context_stack.append(prelude)
                    continue

                selector = prelude
                if selector and selector != ":root" and not selector.startswith(("from", "to")) and "%" not in selector:
                    context = " / ".join(
                        context for context in context_stack if not context.startswith("@layer")
                    ) or "root"
                    yield context, selector, f"{name}:{selector_start_line}"
                context_stack.append("{rule}")
                continue

            in_rule = bool(context_stack and context_stack[-1] == "{rule}")
            if not in_rule and not line.startswith("@"):
                if pending_line_number is None:
                    pending_line_number = line_number
                pending_selector_lines.append(line)


def duplicated_selectors_same_context(paths: list[Path]) -> dict[str, dict[str, object]]:
    selector_locations: dict[tuple[str, str], list[str]] = defaultdict(list)

    for context, selector, location in iter_rule_selectors(paths):
        selector_locations[(context, selector)].append(location)

    return {
        f"{context} :: {selector}": {
            "count": len(locations),
            "locations": locations,
        }
        for (context, selector), locations in sorted(selector_locations.items())
        if len(locations) > 1
    }


def split_selector_list(selector: str) -> list[str]:
    selectors = []
    current = []
    depth = 0
    for char in selector:
        if char in "([":
            depth += 1
        elif char in ")]" and depth:
            depth -= 1
        if char == "," and depth == 0:
            selectors.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    selectors.append("".join(current).strip())
    return [item for item in selectors if item]


def normalize_selector_group(selector: str) -> str | None:
    selectors = [" ".join(item.split()) for item in split_selector_list(selector)]
    if len(selectors) < 2:
        return None
    return ", ".join(sorted(selectors))


def duplicated_selector_groups_same_context(paths: list[Path]) -> dict[str, dict[str, object]]:
    group_locations: dict[tuple[str, str], list[str]] = defaultdict(list)

    for context, selector, location in iter_rule_selectors(paths):
        normalized_group = normalize_selector_group(selector)
        if normalized_group:
            group_locations[(context, normalized_group)].append(location)

    return {
        f"{context} :: {selector_group}": {
            "count": len(locations),
            "locations": locations,
        }
        for (context, selector_group), locations in sorted(group_locations.items())
        if len(locations) > 1
    }


def frontend_runtime_sources(frontend_dir: Path) -> str:
    source_paths = [
        path
        for path in frontend_dir.rglob("*")
        if path.is_file()
        and path.suffix in {".html", ".js"}
        and "css" not in path.parts
    ]
    return "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in source_paths)


def selector_class_locations(paths: list[Path]) -> dict[str, list[str]]:
    class_locations: dict[str, list[str]] = defaultdict(list)
    for _context, selector, location in iter_rule_selectors(paths):
        for class_name in CLASS_SELECTOR_RE.findall(selector):
            class_locations[class_name].append(location)
    return {
        class_name: locations
        for class_name, locations in sorted(class_locations.items())
    }


def selector_id_locations(paths: list[Path]) -> dict[str, list[str]]:
    id_locations: dict[str, list[str]] = defaultdict(list)
    for _context, selector, location in iter_rule_selectors(paths):
        for id_name in ID_SELECTOR_RE.findall(selector):
            id_locations[id_name].append(location)
    return {
        id_name: locations
        for id_name, locations in sorted(id_locations.items())
    }


def source_mentions_class(source: str, class_name: str) -> bool:
    return re.search(
        rf"(?<![A-Za-z0-9_-]){re.escape(class_name)}(?![A-Za-z0-9_-])",
        source,
    ) is not None


def source_mentions_identifier(source: str, identifier: str) -> bool:
    return re.search(
        rf"(?<![A-Za-z0-9_-]){re.escape(identifier)}(?![A-Za-z0-9_-])",
        source,
    ) is not None


def unreferenced_css_classes(
    frontend_dir: Path,
    *,
    allowed_dynamic_classes: set[str] | None = None,
) -> dict[str, list[str]]:
    allowed = DYNAMIC_RUNTIME_CLASSES | (allowed_dynamic_classes or set())
    runtime_source = frontend_runtime_sources(frontend_dir)
    class_locations = selector_class_locations(active_css_paths(frontend_dir))
    return {
        class_name: locations
        for class_name, locations in class_locations.items()
        if class_name not in allowed and not source_mentions_class(runtime_source, class_name)
    }


def unreferenced_css_ids(
    frontend_dir: Path,
    *,
    allowed_dynamic_ids: set[str] | None = None,
) -> dict[str, list[str]]:
    allowed = DYNAMIC_RUNTIME_IDS | (allowed_dynamic_ids or set())
    runtime_source = frontend_runtime_sources(frontend_dir)
    id_locations = selector_id_locations(active_css_paths(frontend_dir))
    return {
        id_name: locations
        for id_name, locations in id_locations.items()
        if id_name not in allowed and not source_mentions_identifier(runtime_source, id_name)
    }


def css_metrics(paths: list[Path]) -> dict[str, object]:
    files = []
    token_locations: dict[str, list[str]] = {}
    important_total = 0
    line_total = 0
    root_total = 0
    legacy_state_class_total = 0

    for path in paths:
        name = css_display_name(path)
        text = path.read_text(encoding="utf-8")
        css_without_comments = strip_comments(text)
        lines = text.count("\n") + 1
        important = text.count("!important")
        roots = len(ROOT_RE.findall(text))
        tokens = TOKEN_RE.findall(text)
        legacy_state_class_total += len(LEGACY_STATE_CLASS_RE.findall(css_without_comments))
        line_total += lines
        important_total += important
        root_total += roots
        for token in tokens:
            token_locations.setdefault(token, []).append(name)
        files.append(
            {
                "name": name,
                "lines": lines,
                "important": important,
                "root_blocks": roots,
                "token_declarations": len(tokens),
                "unique_tokens": len(set(tokens)),
            }
        )

    duplicated_tokens = {
        token: sorted(set(locations))
        for token, locations in token_locations.items()
        if len(set(locations)) > 1
    }

    return {
        "files": files,
        "total_lines": line_total,
        "total_important": important_total,
        "total_root_blocks": root_total,
        "legacy_state_class_selectors": legacy_state_class_total,
        "unique_tokens": len(token_locations),
        "duplicated_tokens_across_files": duplicated_tokens,
        "duplicated_selectors_same_context": duplicated_selectors_same_context(paths),
        "duplicated_selector_groups_same_context": duplicated_selector_groups_same_context(paths),
    }


def build_payload(project_root: Path) -> dict[str, object]:
    frontend_dir = project_root / "apps" / "flatshot-desktop" / "frontend"
    paths = active_css_paths(frontend_dir)
    return {
        "linked_stylesheets": linked_stylesheets(frontend_dir / "index.html"),
        "versions": sorted(stylesheet_versions(frontend_dir / "index.html")),
        "metrics": css_metrics(paths),
        "unreferenced_css_classes": unreferenced_css_classes(frontend_dir),
        "unreferenced_css_ids": unreferenced_css_ids(frontend_dir),
        "layer": CSS_LAYER_NAME,
        "legacy_compat_empty": legacy_compat_payload(frontend_dir / "css" / "99-legacy-compat.css") == "",
    }


def css_contract_failures(project_root: Path, payload: dict[str, object]) -> list[str]:
    frontend_dir = project_root / "apps" / "flatshot-desktop" / "frontend"
    paths = active_css_paths(frontend_dir)
    metrics = payload["metrics"]
    assert isinstance(metrics, dict)

    failures: list[str] = []
    linked = payload["linked_stylesheets"]
    if linked != CSS_MODULE_ORDER:
        failures.append("CSS links must match CSS_MODULE_ORDER exactly.")

    linked_names = {Path(str(link)).name for link in linked}
    if linked_names & LEGACY_STYLESHEETS:
        failures.append("Legacy stylesheets must not be linked.")
    for legacy_stylesheet in LEGACY_STYLESHEETS:
        if (frontend_dir / legacy_stylesheet).exists():
            failures.append(f"Legacy stylesheet still exists: {legacy_stylesheet}.")

    if metrics["total_lines"] > CSS_TOTAL_LINE_LIMIT:
        failures.append(f"CSS line count exceeds {CSS_TOTAL_LINE_LIMIT}.")
    if metrics["total_important"] > CSS_IMPORTANT_LIMIT:
        failures.append(f"!important count exceeds {CSS_IMPORTANT_LIMIT}.")
    if metrics["legacy_state_class_selectors"] != 0:
        failures.append("Legacy shell state selectors are not allowed.")
    if metrics["duplicated_tokens_across_files"]:
        failures.append("Token declarations must not be duplicated across files.")
    if metrics["duplicated_selectors_same_context"]:
        failures.append("Duplicate selectors in the same cascade context are not allowed.")
    if metrics["duplicated_selector_groups_same_context"]:
        failures.append("Duplicate selector groups in the same cascade context are not allowed.")
    if payload["unreferenced_css_classes"]:
        failures.append("Active CSS classes must be referenced by runtime HTML/JS or explicitly allowlisted.")
    if payload["unreferenced_css_ids"]:
        failures.append("Active CSS ids must be referenced by runtime HTML/JS or explicitly allowlisted.")
    if not payload["legacy_compat_empty"]:
        failures.append("css/99-legacy-compat.css must stay empty.")

    file_metrics = metrics["files"]
    assert isinstance(file_metrics, list)
    too_large = [
        str(item["name"])
        for item in file_metrics
        if isinstance(item, dict) and item["lines"] > CSS_FILE_LINE_LIMIT
    ]
    if too_large:
        failures.append(f"CSS modules exceed {CSS_FILE_LINE_LIMIT} lines: {', '.join(too_large)}.")

    for path in paths:
        if path.name == "99-legacy-compat.css":
            continue
        layer, payload_text = css_layer_payload(path)
        if layer != CSS_LAYER_NAME:
            failures.append(f"{css_display_name(path)} must stay in @layer {CSS_LAYER_NAME}.")
        if "{" not in payload_text:
            failures.append(f"{css_display_name(path)} is linked but has no active rules.")

    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit FlatShot frontend CSS cascade contract.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with a non-zero status when the CSS cascade contract is violated.",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    payload = build_payload(project_root)
    print(json.dumps(payload, indent=2, sort_keys=True))
    if args.check:
        failures = css_contract_failures(project_root, payload)
        if failures:
            print("\nCSS audit failed:", file=sys.stderr)
            for failure in failures:
                print(f"- {failure}", file=sys.stderr)
            raise SystemExit(1)


if __name__ == "__main__":
    main()
