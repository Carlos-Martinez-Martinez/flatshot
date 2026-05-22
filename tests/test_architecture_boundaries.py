import ast
from pathlib import Path

import flatshot.application.export_runner as export_runner
import flatshot.workers.export_worker as export_worker


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src" / "flatshot"
PROTECTED_PACKAGE_DIRS = (
    SRC_ROOT / "application",
    SRC_ROOT / "core",
)

QT_IMPORT_ROOTS = {
    "PyQt6",
    "PyQt5",
    "PySide6",
    "PySide2",
}

DISALLOWED_INTERNAL_PREFIXES = (
    "flatshot.ui",
    "flatshot.workers",
)

DISALLOWED_INTERNAL_MODULES = {
    "flatshot.utils.config",
    "flatshot.utils.log_manager",
}

# Keep temporary exceptions explicit. There are none at the moment.
IMPORT_ALLOWLIST: dict[str, set[str]] = {}


def _protected_python_files():
    for package_dir in PROTECTED_PACKAGE_DIRS:
        yield from sorted(package_dir.rglob("*.py"))


def _relative(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def _imports_from(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def _is_disallowed(module_name: str) -> bool:
    root = module_name.split(".", 1)[0]
    if root in QT_IMPORT_ROOTS:
        return True
    if module_name in DISALLOWED_INTERNAL_MODULES:
        return True
    if any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for prefix in DISALLOWED_INTERNAL_PREFIXES
    ):
        return True
    return False


def _is_allowlisted(path: Path, module_name: str) -> bool:
    return module_name in IMPORT_ALLOWLIST.get(_relative(path), set())


def test_application_and_core_do_not_import_qt_or_qt_adapters():
    violations: list[str] = []

    for path in _protected_python_files():
        for module_name in _imports_from(path):
            if _is_disallowed(module_name) and not _is_allowlisted(path, module_name):
                violations.append(f"{_relative(path)} imports {module_name}")

    assert violations == []


def test_export_worker_legacy_helpers_reexport_application_helpers():
    helper_names = [
        "apply_naming_template",
        "build_variant_output_path",
        "get_enabled_export_variants",
        "process_single_image",
        "validate_output_path_collisions",
        "variant_bg_token",
        "variant_export_format",
        "variant_output_folder",
    ]

    for helper_name in helper_names:
        assert getattr(export_worker, helper_name) is getattr(export_runner, helper_name)


def test_local_api_package_is_not_active_yet():
    assert not (SRC_ROOT / "api").exists()
