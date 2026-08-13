from pathlib import Path


project_root = Path(SPECPATH).resolve().parents[1]
launcher = project_root / "scripts" / "portable" / "FlatShot.pyw"
frontend = project_root / "apps" / "flatshot-desktop" / "frontend"

a = Analysis(
    [str(launcher)],
    pathex=[str(project_root / "src"), str(project_root / "scripts" / "portable")],
    binaries=[],
    datas=[(str(frontend), "frontend")],
    hiddenimports=["webview.platforms.edgechromium"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "cefpython3",
        "gtk",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "wx",
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FlatShot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="FlatShot",
    contents_directory="_internal",
)
