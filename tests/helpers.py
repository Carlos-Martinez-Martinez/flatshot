from __future__ import annotations

from concurrent.futures import Future
from pathlib import Path
from typing import Any

from PIL import Image


class InlineExecutor:
    def __init__(self, max_workers: int = 1):
        self.max_workers = max_workers
        self.shutdown_called = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.shutdown()

    def submit(self, fn, arg):
        future = Future()
        try:
            future.set_result(fn(arg))
        except Exception as exc:
            future.set_exception(exc)
        return future

    def shutdown(self, wait: bool = True, cancel_futures: bool = False):
        self.shutdown_called = True


class CollectingSink:
    def __init__(self):
        self.events: list[Any] = []

    def emit(self, event):
        self.events.append(event)


def write_png(path: Path, *, size: tuple[int, int] = (8, 8), color=(255, 0, 0, 255)) -> Path:
    Image.new("RGBA", size, color).save(path)
    return path
