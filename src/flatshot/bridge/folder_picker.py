"""Native folder picker adapter for the local bridge."""

from __future__ import annotations

from pathlib import Path

from flatshot.bridge.errors import BridgeError


def pick_folder_with_tk(initial_path: Path | None = None) -> Path | None:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception as exc:
        raise BridgeError("folder_picker_unavailable", "Selector de carpeta no disponible.", status=503) from exc

    root = tk.Tk()
    root.withdraw()
    root.update()
    try:
        try:
            root.attributes("-topmost", True)
        except tk.TclError:
            pass
        selected = filedialog.askdirectory(
            parent=root,
            title="Seleccionar carpeta FlatShot",
            initialdir=str(initial_path or Path.home()),
            mustexist=True,
        )
    finally:
        root.destroy()

    return Path(selected).expanduser() if selected else None
