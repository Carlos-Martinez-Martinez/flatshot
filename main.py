"""
Convenience launcher for FlatShot.

Allows running the app with:
    python main.py
without requiring an editable install first.
"""
from pathlib import Path
import sys


def _ensure_src_on_path():
    root = Path(__file__).resolve().parent
    src = root / "src"
    src_str = str(src)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)


def main():
    _ensure_src_on_path()
    from flatshot.__main__ import main as entrypoint
    entrypoint()


if __name__ == "__main__":
    main()
