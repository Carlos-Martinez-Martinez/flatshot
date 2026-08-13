"""Verify a packaged FlatShot portable in a clean extraction directory."""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import zipfile
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_portable


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify a frozen FlatShot portable candidate.")
    parser.add_argument("archive", type=Path)
    parser.add_argument("checksums", type=Path)
    parser.add_argument("--extract-to", type=Path, required=True)
    parser.add_argument("--forbid-root", type=Path, action="append", default=[])
    parser.add_argument("--skip-smoke", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    portable = verify_candidate(
        args.archive.expanduser().resolve(),
        args.checksums.expanduser().resolve(),
        args.extract_to.expanduser().resolve(),
        forbidden_roots=[path.expanduser().resolve() for path in args.forbid_root],
        execute_smoke=not args.skip_smoke,
    )
    print(f"Verified portable candidate: {portable}")
    return 0


def verify_checksum(archive: Path, checksums: Path) -> str:
    expected = None
    for line in checksums.read_text(encoding="ascii").splitlines():
        parts = line.strip().split(maxsplit=1)
        if len(parts) == 2 and parts[1].lstrip("*") == archive.name:
            expected = parts[0].casefold()
            break
    actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    if expected is None or expected != actual:
        raise RuntimeError(f"Portable checksum mismatch for {archive.name}: expected={expected}, actual={actual}")
    return actual


def extract_archive(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()):
        raise RuntimeError(f"Extraction destination must be empty: {destination}")
    root = destination.resolve()
    with zipfile.ZipFile(archive) as bundle:
        for info in bundle.infolist():
            member = Path(info.filename.replace("\\", "/"))
            if member.is_absolute() or ".." in member.parts:
                raise RuntimeError(f"unsafe archive path: {info.filename}")
            extracted = (root / member).resolve()
            if not extracted.is_relative_to(root):
                raise RuntimeError(f"unsafe archive path: {info.filename}")
        bundle.extractall(root)


def sanitized_portable_environment() -> dict[str, str]:
    env = os.environ.copy()
    for name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        env.pop(name, None)
    system_root = env.get("SystemRoot", r"C:\Windows").rstrip("\\/")
    env["PATH"] = os.pathsep.join(
        [
            system_root,
            f"{system_root}/System32",
            f"{system_root}/System32/Wbem",
        ]
    )
    env["PYTHONNOUSERSITE"] = "1"
    return env


def run_frozen_smoke(portable: Path) -> subprocess.CompletedProcess[str]:
    executable = portable / "FlatShot.exe"
    try:
        completed = subprocess.run(
            [str(executable), "--smoke"],
            cwd=str(portable),
            env=sanitized_portable_environment(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(f"Frozen portable smoke could not run: {error}") from error
    if completed.returncode != 0:
        output = (completed.stdout or "").strip()[-4000:]
        raise RuntimeError(f"Frozen portable smoke failed with exit code {completed.returncode}:\n{output}")
    return completed


def verify_candidate(
    archive: Path,
    checksums: Path,
    extraction_root: Path,
    *,
    forbidden_roots: list[Path] | tuple[Path, ...] = (),
    execute_smoke: bool = True,
) -> Path:
    verify_checksum(archive, checksums)
    extract_archive(archive, extraction_root)
    portable = (extraction_root / "FlatShotPortable").resolve()
    build_portable.validate_release_portable(portable, forbidden_roots=forbidden_roots)
    if execute_smoke:
        run_frozen_smoke(portable)
    return portable


if __name__ == "__main__":
    raise SystemExit(main())
