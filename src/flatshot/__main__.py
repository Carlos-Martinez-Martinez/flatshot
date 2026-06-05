"""FlatShot package entry point.

The desktop UI lives in apps/flatshot-desktop and is started with the project
runner. The installed ``flatshot`` command remains a Qt-free CLI for automation.
"""
from __future__ import annotations

from flatshot.cli import main


if __name__ == "__main__":
    main()
