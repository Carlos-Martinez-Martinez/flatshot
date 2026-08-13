"""Build and package the Windows frozen portable release candidate."""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import zipfile
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_portable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PORTABLE = PROJECT_ROOT / "release" / "FlatShotPortable"
DEFAULT_OUTPUT = PROJECT_ROOT / "release"
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the exact Windows portable release candidate.")
    parser.add_argument("--version", required=True, help="Semantic version without the v prefix.")
    parser.add_argument("--portable-dir", type=Path, default=DEFAULT_PORTABLE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--skip-build", action="store_true", help="Package an already-built frozen portable.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not VERSION_RE.fullmatch(args.version):
        raise RuntimeError(f"Invalid release version: {args.version}")
    portable = args.portable_dir.expanduser().resolve()
    if not args.skip_build:
        build_portable.build_release_portable(PROJECT_ROOT, portable)
    build_portable.validate_release_portable(portable, forbidden_roots=[PROJECT_ROOT])
    archive, sums = package_portable(portable, args.output_dir.expanduser().resolve(), args.version)
    print(f"Release candidate: {archive}")
    print(f"Checksums: {sums}")
    return 0


def package_portable(portable: Path, output_dir: Path, version: str) -> tuple[Path, Path]:
    if not VERSION_RE.fullmatch(version):
        raise RuntimeError(f"Invalid release version: {version}")
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"FlatShotPortable-v{version}.zip"
    sums = output_dir / "SHA256SUMS.txt"
    archive.unlink(missing_ok=True)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in sorted(portable.rglob("*")):
            relative = path.relative_to(portable)
            archive_name = (Path(portable.name) / relative).as_posix()
            if path.is_dir():
                bundle.writestr(archive_name.rstrip("/") + "/", b"")
            else:
                bundle.write(path, archive_name)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    sums.write_text(f"{digest}  {archive.name}\n", encoding="ascii", newline="\n")
    return archive, sums


if __name__ == "__main__":
    raise SystemExit(main())
