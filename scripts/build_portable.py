"""Build or refresh the local FlatShot portable folder."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
import venv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = PROJECT_ROOT / "release" / "FlatShotPortable"
LAUNCHER_TEMPLATE = PROJECT_ROOT / "scripts" / "portable" / "FlatShot.pyw"
RUNTIME_SOURCE_DIRS = (
    Path("src") / "flatshot",
    Path("apps") / "flatshot-desktop" / "frontend",
)
DEPENDENCY_FILES = ("pyproject.toml", "requirements.txt")
PORTABLE_DEPENDENCIES = ("pywebview>=6.0",)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="build-flatshot-portable",
        description="Crea o actualiza release/FlatShotPortable.",
    )
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--skip-venv", action="store_true", help="No crea ni actualiza el venv portable.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    target = args.target.expanduser().resolve()
    build_portable(PROJECT_ROOT, target, install_dependencies=not args.skip_venv)
    print(f"Portable listo: {target}")
    print(f"Launcher: {target / 'Abrir FlatShot.vbs'}")
    return 0


def build_portable(source_root: Path, target: Path, *, install_dependencies: bool = True) -> None:
    validate_source_root(source_root)
    target.mkdir(parents=True, exist_ok=True)
    (target / "data").mkdir(exist_ok=True)
    (target / "portable.flag").write_text("portable\n", encoding="utf-8")
    (target / "source_path.txt").write_text(str(source_root), encoding="utf-8")

    sync_portable_app(source_root, target)
    copy_launcher_files(target)
    write_sync_stamp(source_root, target)

    if install_dependencies:
        ensure_portable_venv(source_root, target / "venv")


def validate_source_root(source_root: Path) -> None:
    required = [
        source_root / "pyproject.toml",
        source_root / "requirements.txt",
        source_root / "src" / "flatshot" / "bridge" / "service.py",
        source_root / "apps" / "flatshot-desktop" / "frontend" / "index.html",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("No es una raiz valida de FlatShot:\n" + "\n".join(missing))


def sync_portable_app(source_root: Path, target: Path) -> None:
    app_dir = target / "app"
    app_dir.mkdir(parents=True, exist_ok=True)
    copy_tree(source_root / "src" / "flatshot", app_dir / "flatshot")
    copy_tree(source_root / "apps" / "flatshot-desktop" / "frontend", app_dir / "frontend")


def copy_launcher_files(target: Path) -> None:
    shutil.copy2(LAUNCHER_TEMPLATE, target / "FlatShot.pyw")
    (target / "Abrir FlatShot.vbs").write_text(VBS_LAUNCHER, encoding="utf-8")
    (target / "Diagnostico FlatShot.bat").write_text(DIAGNOSTIC_BAT, encoding="utf-8")
    (target / "README_PORTABLE.txt").write_text(README_PORTABLE, encoding="utf-8")


def ensure_portable_venv(source_root: Path, venv_dir: Path) -> None:
    python_exe = portable_python(venv_dir)
    if not python_exe.exists():
        venv.EnvBuilder(with_pip=True, clear=False).create(venv_dir)

    run_command([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"], source_root, timeout=300)
    run_command([str(python_exe), "-m", "pip", "install", "-r", str(source_root / "requirements.txt")], source_root, timeout=300)
    run_command([str(python_exe), "-m", "pip", "install", *PORTABLE_DEPENDENCIES], source_root, timeout=300)


def portable_python(venv_dir: Path) -> Path:
    if sys.platform.startswith("win"):
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def run_command(command: list[str], cwd: Path, *, timeout: int) -> None:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    if completed.returncode != 0:
        output = (completed.stdout or "").strip()[-4000:]
        raise RuntimeError(f"Comando fallido ({' '.join(command)}):\n{output}")


def copy_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=ignore_generated)


def ignore_generated(_directory: str, names: list[str]) -> set[str]:
    ignored = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules", "build", "dist"}
    return {name for name in names if name in ignored or name.endswith((".pyc", ".pyo", ".tsbuildinfo"))}


def source_manifest_hash(source_root: Path) -> str:
    return files_manifest_hash(iter_source_files(source_root), source_root)


def runtime_manifest_hash(source_root: Path) -> str:
    return files_manifest_hash(iter_runtime_source_files(source_root), source_root)


def dependency_manifest_hash(source_root: Path) -> str:
    digest = hashlib.sha256()
    digest.update(files_manifest_hash(iter_dependency_files(source_root), source_root).encode("utf-8"))
    for dependency in PORTABLE_DEPENDENCIES:
        digest.update(f"\0portable:{dependency}\n".encode("utf-8"))
    return digest.hexdigest()


def files_manifest_hash(files, source_root: Path) -> str:
    digest = hashlib.sha256()
    for file in files:
        stat = file.stat()
        rel = file.relative_to(source_root).as_posix()
        digest.update(f"{rel}\0{stat.st_size}\0{stat.st_mtime_ns}\n".encode("utf-8"))
    return digest.hexdigest()


def iter_source_files(source_root: Path):
    yield from iter_runtime_source_files(source_root)
    yield from iter_dependency_files(source_root)


def iter_runtime_source_files(source_root: Path):
    for source_dir in RUNTIME_SOURCE_DIRS:
        root = source_root / source_dir
        for file in root.rglob("*"):
            if should_skip_source_file(file):
                continue
            if file.is_file():
                yield file


def iter_dependency_files(source_root: Path):
    for file_name in DEPENDENCY_FILES:
        file = source_root / file_name
        if file.exists() and file.is_file():
            yield file


def should_skip_source_file(file: Path) -> bool:
    parts = set(file.parts)
    if {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "release", "venv", ".venv"} & parts:
        return True
    return file.suffix in {".pyc", ".pyo"} or file.name.endswith(".tsbuildinfo")


def write_sync_stamp(source_root: Path, target: Path) -> None:
    (target / ".autosync.json").write_text(
        json.dumps(
            {
                "source_root": str(source_root),
                "manifest_hash": source_manifest_hash(source_root),
                "runtime_hash": runtime_manifest_hash(source_root),
                "dependency_hash": dependency_manifest_hash(source_root),
                "portable_dependencies": list(PORTABLE_DEPENDENCIES),
                "dependency_status": "current",
                "synced_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


VBS_LAUNCHER = '''Option Explicit

Dim shell, fso, appDir, pythonw, launcher
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

appDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonw = fso.BuildPath(appDir, "venv\\Scripts\\pythonw.exe")
launcher = fso.BuildPath(appDir, "FlatShot.pyw")

If Not fso.FileExists(pythonw) Then
  MsgBox "No se encontro pythonw.exe en:" & vbCrLf & pythonw, vbCritical, "FlatShot"
  WScript.Quit 1
End If

If Not fso.FileExists(launcher) Then
  MsgBox "No se encontro el launcher en:" & vbCrLf & launcher, vbCritical, "FlatShot"
  WScript.Quit 1
End If

shell.CurrentDirectory = appDir
shell.Run """" & pythonw & """ """ & launcher & """", 0, False
'''


DIAGNOSTIC_BAT = """@echo off
setlocal
set "APPDIR=%~dp0"
pushd "%APPDIR%"
echo Arrancando FlatShot en modo diagnostico...
echo.
venv\\Scripts\\python.exe "FlatShot.pyw"
echo.
echo Si hubo un error, copia o captura el texto anterior.
pause
"""


README_PORTABLE = """FlatShot Portable

Ejecutar:
  Abrir FlatShot.vbs

Diagnostico con consola:
  Diagnostico FlatShot.bat

Datos locales del portable:
  data\\

Ventana:
  FlatShot se abre en una ventana propia con WebView2/pywebview. Si la ventana
  nativa no puede iniciarse, se abre en el navegador como fallback.

Live reload:
  Si source_path.txt apunta al repo, la ventana sirve la interfaz directamente
  desde apps\\flatshot-desktop\\frontend y se recarga al cambiar HTML, CSS o JS.
  Para desactivarlo, arranca con FLATSHOT_LIVE_RELOAD=0.

Actualizacion:
  Si este portable esta dentro de release\\FlatShotPortable, al arrancar se
  sincroniza automaticamente desde el repo indicado en source_path.txt cuando
  detecta cambios de codigo o frontend.

  Si cambian dependencias de Python, vuelve a ejecutar desde el repo:
    python scripts\\build_portable.py
"""


if __name__ == "__main__":
    raise SystemExit(main())
