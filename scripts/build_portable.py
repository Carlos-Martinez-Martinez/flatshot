"""Build or refresh the local FlatShot portable folder."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import shutil
import subprocess
import sys
import tempfile
import time
import venv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from portable.manifest import (  # noqa: E402
    PORTABLE_DEPENDENCIES,
    dependency_manifest_hash,
    iter_runtime_source_files,
    iter_source_files,
    runtime_manifest_hash,
    source_manifest_hash,
)
from portable.runtime_sync import sync_runtime_app  # noqa: E402

DEFAULT_TARGET = PROJECT_ROOT / "release" / "FlatShotPortable"
LAUNCHER_TEMPLATE = PROJECT_ROOT / "scripts" / "portable" / "FlatShot.pyw"
MANIFEST_TEMPLATE = PROJECT_ROOT / "scripts" / "portable" / "manifest.py"
RUNTIME_SYNC_TEMPLATE = PROJECT_ROOT / "scripts" / "portable" / "runtime_sync.py"
PYINSTALLER_SPEC = PROJECT_ROOT / "scripts" / "portable" / "FlatShot.spec"
TEXT_CONFIG_SUFFIXES = {
    ".bat",
    ".cfg",
    ".cmd",
    ".ini",
    ".json",
    ".ps1",
    ".py",
    ".pyw",
    ".toml",
    ".txt",
    ".vbs",
    ".xml",
    ".yaml",
    ".yml",
}
FROZEN_LICENSE_DISTRIBUTIONS = (
    "altgraph",
    "annotated-types",
    "bottle",
    "cffi",
    "clr-loader",
    "numpy",
    "pefile",
    "Pillow",
    "proxy-tools",
    "pycparser",
    "pydantic",
    "pydantic-core",
    "PyInstaller",
    "pyinstaller-hooks-contrib",
    "pythonnet",
    "pywebview",
    "pywin32-ctypes",
    "setuptools",
    "typing-extensions",
    "typing-inspection",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="build-flatshot-portable",
        description="Crea o actualiza release/FlatShotPortable.",
    )
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--skip-venv", action="store_true", help="No crea ni actualiza el venv portable.")
    parser.add_argument(
        "--release",
        action="store_true",
        help="Construye un portable autocontenido sin puntero al repositorio de desarrollo.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    target = args.target.expanduser().resolve()
    build_portable(
        PROJECT_ROOT,
        target,
        install_dependencies=not args.skip_venv,
        development=not args.release,
    )
    print(f"Portable listo: {target}")
    print(f"Launcher: {target / ('FlatShot.exe' if args.release else 'Abrir FlatShot.vbs')}")
    return 0


def build_portable(
    source_root: Path,
    target: Path,
    *,
    install_dependencies: bool = True,
    development: bool = True,
) -> None:
    if not development:
        build_release_portable(source_root, target)
        return

    build_development_portable(
        source_root,
        target,
        install_dependencies=install_dependencies,
    )


def build_development_portable(
    source_root: Path,
    target: Path,
    *,
    install_dependencies: bool = True,
) -> None:
    validate_source_root(source_root)
    target.mkdir(parents=True, exist_ok=True)
    (target / "data").mkdir(exist_ok=True)
    (target / "portable.flag").write_text("portable\n", encoding="utf-8")
    source_pointer = target / "source_path.txt"
    development_flag = target / "development.flag"
    source_pointer.write_text(str(source_root), encoding="utf-8")
    development_flag.write_text("development\n", encoding="utf-8")
    (target / "release.flag").unlink(missing_ok=True)

    sync_portable_app(source_root, target)
    copy_launcher_files(target)
    write_sync_stamp(source_root, target, development=True)

    if install_dependencies:
        ensure_portable_venv(source_root, target / "venv")


def build_release_portable(source_root: Path, target: Path) -> None:
    validate_source_root(source_root)
    if not sys.platform.startswith("win"):
        raise RuntimeError("El portable frozen de release solo se construye en Windows.")
    with tempfile.TemporaryDirectory(prefix="flatshot-release-build-") as temporary:
        staging = Path(temporary)
        dist_dir = staging / "dist"
        work_dir = staging / "work"
        run_command(
            [
                sys.executable,
                "-m",
                "PyInstaller",
                "--noconfirm",
                "--clean",
                "--distpath",
                str(dist_dir),
                "--workpath",
                str(work_dir),
                str(PYINSTALLER_SPEC),
            ],
            source_root,
            timeout=1200,
        )
        frozen_root = dist_dir / "FlatShot"
        write_release_support_files(frozen_root)
        validate_release_portable(frozen_root, forbidden_roots=[source_root, staging])
        if target.exists():
            shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(frozen_root, target)
    validate_release_portable(target, forbidden_roots=[source_root])


def write_release_support_files(target: Path, source_root: Path = PROJECT_ROOT) -> None:
    target.mkdir(parents=True, exist_ok=True)
    (target / "data").mkdir(exist_ok=True)
    (target / "portable.flag").write_text("portable\n", encoding="utf-8")
    (target / "release.flag").write_text("release\n", encoding="utf-8")
    for forbidden in ("source_path.txt", "development.flag", ".autosync.json"):
        (target / forbidden).unlink(missing_ok=True)
    (target / "Abrir FlatShot.vbs").write_text(RELEASE_VBS_LAUNCHER, encoding="utf-8")
    (target / "Diagnostico FlatShot.bat").write_text(RELEASE_DIAGNOSTIC_BAT, encoding="utf-8")
    (target / "README_PORTABLE.txt").write_text(RELEASE_README_PORTABLE, encoding="utf-8")
    shutil.copy2(source_root / "LICENSE", target / "LICENSE.txt")
    shutil.copy2(source_root / "THIRD_PARTY_NOTICES.md", target / "THIRD_PARTY_NOTICES.txt")
    copy_frozen_runtime_licenses(target)


def copy_frozen_runtime_licenses(
    target: Path,
    *,
    python_license: Path | None = None,
    distribution_licenses: dict[str, list[Path]] | None = None,
) -> int:
    licenses_root = target / "THIRD_PARTY_LICENSES"
    if licenses_root.exists():
        shutil.rmtree(licenses_root)
    licenses_root.mkdir(parents=True)
    copied = 0

    python_license = python_license or (Path(sys.base_prefix) / "LICENSE.txt")
    if python_license.is_file():
        destination = licenses_root / "CPython" / python_license.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(python_license, destination)
        copied += 1

    distribution_licenses = distribution_licenses or find_distribution_license_files()
    for distribution_name, license_files in sorted(distribution_licenses.items()):
        destination_dir = licenses_root / distribution_name
        for index, license_file in enumerate(license_files, start=1):
            if not license_file.is_file():
                continue
            destination_dir.mkdir(parents=True, exist_ok=True)
            destination_name = license_file.name
            destination = destination_dir / destination_name
            if destination.exists():
                destination = destination_dir / f"{index}-{destination_name}"
            shutil.copy2(license_file, destination)
            copied += 1
    if copied == 0:
        raise RuntimeError("No se encontraron licencias para el runtime frozen.")
    return copied


def find_distribution_license_files() -> dict[str, list[Path]]:
    result: dict[str, list[Path]] = {}
    for requested_name in FROZEN_LICENSE_DISTRIBUTIONS:
        try:
            distribution = importlib.metadata.distribution(requested_name)
        except importlib.metadata.PackageNotFoundError:
            continue
        name = distribution.metadata.get("Name", requested_name)
        version = distribution.version
        key = f"{name}-{version}".replace("/", "-").replace("\\", "-")
        files: list[Path] = []
        for entry in distribution.files or ():
            filename = Path(str(entry)).name.casefold()
            if not filename.startswith(("license", "copying", "notice", "authors")):
                continue
            located = Path(distribution.locate_file(entry)).resolve()
            if located.is_file():
                files.append(located)
        if files:
            result[key] = files
    return result


def validate_release_portable(target: Path, *, forbidden_roots: list[Path] | tuple[Path, ...] = ()) -> None:
    required = [
        target / "FlatShot.exe",
        target / "_internal",
        target / "_internal" / "frontend" / "index.html",
        target / "Abrir FlatShot.vbs",
        target / "Diagnostico FlatShot.bat",
        target / "README_PORTABLE.txt",
        target / "LICENSE.txt",
        target / "THIRD_PARTY_NOTICES.txt",
        target / "THIRD_PARTY_LICENSES",
        target / "data",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError("Release portable incompleto:\n" + "\n".join(missing))

    forbidden_names = {"pyvenv.cfg", "source_path.txt", "development.flag"}
    for path in target.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(target)
        lowered_parts = [part.casefold() for part in relative.parts]
        if path.name.casefold() in forbidden_names or (
            "venv" in lowered_parts and path.name.casefold() in {"python.exe", "pythonw.exe"}
        ):
            raise RuntimeError(f"Release portable non-relocatable: {relative.as_posix()}")

    markers = ["hostedtoolcache", "runner_workspace", "github_workspace"]
    for root in forbidden_roots:
        resolved = str(root.expanduser().resolve())
        markers.extend([resolved, resolved.replace("\\", "/"), resolved.replace("\\", "\\\\")])
    normalized_markers = [marker.casefold() for marker in markers if marker]
    for path in target.rglob("*"):
        if not path.is_file() or path.suffix.casefold() not in TEXT_CONFIG_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        lowered = text.casefold()
        if any(marker in lowered for marker in normalized_markers):
            raise RuntimeError(f"Release portable contiene builder path en {path.relative_to(target).as_posix()}")


def validate_source_root(source_root: Path) -> None:
    required = [
        source_root / "pyproject.toml",
        source_root / "requirements.txt",
        source_root / "requirements.lock",
        source_root / "src" / "flatshot" / "bridge" / "service.py",
        source_root / "apps" / "flatshot-desktop" / "frontend" / "index.html",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("No es una raiz valida de FlatShot:\n" + "\n".join(missing))


def sync_portable_app(source_root: Path, target: Path) -> None:
    sync_runtime_app(source_root, target / "app")


def copy_launcher_files(target: Path) -> None:
    shutil.copy2(LAUNCHER_TEMPLATE, target / "FlatShot.pyw")
    shutil.copy2(MANIFEST_TEMPLATE, target / "manifest.py")
    shutil.copy2(RUNTIME_SYNC_TEMPLATE, target / "runtime_sync.py")
    (target / "Abrir FlatShot.vbs").write_text(VBS_LAUNCHER, encoding="utf-8")
    (target / "Diagnostico FlatShot.bat").write_text(DIAGNOSTIC_BAT, encoding="utf-8")
    (target / "README_PORTABLE.txt").write_text(README_PORTABLE, encoding="utf-8")


def ensure_portable_venv(source_root: Path, venv_dir: Path) -> None:
    python_exe = portable_python(venv_dir)
    if not python_exe.exists():
        venv.EnvBuilder(with_pip=True, clear=False).create(venv_dir)

    run_command([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"], source_root, timeout=300)
    runtime_requirements = source_root / "requirements.lock"
    if not runtime_requirements.exists():
        runtime_requirements = source_root / "requirements.txt"
    run_command([str(python_exe), "-m", "pip", "install", "-r", str(runtime_requirements)], source_root, timeout=300)
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


def write_sync_stamp(source_root: Path, target: Path, *, development: bool = True) -> None:
    (target / ".autosync.json").write_text(
        json.dumps(
            {
                "source_root": str(source_root) if development else None,
                "portable_mode": "development" if development else "release",
                "manifest_hash": source_manifest_hash(source_root),
                "runtime_hash": runtime_manifest_hash(source_root),
                "dependency_hash": dependency_manifest_hash(source_root),
                "portable_dependencies": list(PORTABLE_DEPENDENCIES),
                "dependency_status": "current",
                "python_version": sys.version.split()[0],
                "synced_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


RELEASE_VBS_LAUNCHER = '''Option Explicit

Dim shell, fso, appDir, executable
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

appDir = fso.GetParentFolderName(WScript.ScriptFullName)
executable = fso.BuildPath(appDir, "FlatShot.exe")

If Not fso.FileExists(executable) Then
  MsgBox "No se encontro FlatShot.exe en:" & vbCrLf & executable, vbCritical, "FlatShot"
  WScript.Quit 1
End If

shell.CurrentDirectory = appDir
shell.Run """" & executable & """", 0, False
'''


RELEASE_DIAGNOSTIC_BAT = r"""@echo off
setlocal
set "APPDIR=%~dp0"
pushd "%APPDIR%"
echo Validando el runtime autocontenido de FlatShot...
echo.
"%APPDIR%FlatShot.exe" --smoke
set "RESULT=%ERRORLEVEL%"
echo.
if exist "%APPDIR%data\logs\runtime.log" (
  echo Ultimas entradas del log:
  type "%APPDIR%data\logs\runtime.log"
)
echo.
if not "%RESULT%"=="0" echo El diagnostico fallo con codigo %RESULT%.
if "%RESULT%"=="0" echo Diagnostico completado correctamente.
pause
exit /b %RESULT%
"""


RELEASE_README_PORTABLE = r"""FlatShot Portable

Ejecutar:
  Abrir FlatShot.vbs

Diagnostico sin abrir la interfaz:
  Diagnostico FlatShot.bat
  FlatShot.exe --smoke

Datos locales del portable:
  data\

Este release incluye su propio runtime de Python y no requiere Python, PATH,
un entorno virtual ni acceso al repositorio en el equipo de destino. Conserva
toda la carpeta extraida, incluido _internal, junto a FlatShot.exe.

Los errores de arranque se registran en data\logs\runtime.log.
"""


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
  Antes de recargar guarda un snapshot de sesion para recuperar lote, imagen
  seleccionada, filtros, vista, pestana activa y controles de salida.
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
