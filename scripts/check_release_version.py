"""Check that a release tag agrees with FlatShot's version declarations."""
from __future__ import annotations

import argparse
import re
import tomllib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TAG_RE = re.compile(r"^v(?P<version>\d+\.\d+\.\d+)$")


def validate_release_version(project_root: Path, tag: str) -> str:
    match = TAG_RE.fullmatch(tag.strip())
    if match is None:
        raise ValueError("Release tag must use the form vX.Y.Z.")
    version = match.group("version")
    metadata = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))
    package_version = str(metadata["project"]["version"])
    init_text = (project_root / "src" / "flatshot" / "__init__.py").read_text(encoding="utf-8")
    init_match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', init_text, flags=re.MULTILINE)
    runtime_version = init_match.group(1) if init_match else ""
    if version != package_version or version != runtime_version:
        raise ValueError(
            f"Version mismatch: tag={version}, pyproject={package_version}, runtime={runtime_version or 'missing'}."
        )
    return version


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag", help="Release tag, for example v1.0.0")
    args = parser.parse_args()
    version = validate_release_version(PROJECT_ROOT, args.tag)
    print(f"Release version {version} is consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
