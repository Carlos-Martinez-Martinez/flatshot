"""Qt-free pause and cancellation primitives for background jobs."""
from __future__ import annotations

import threading


class CancellationToken:
    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()


class PauseToken:
    def __init__(self) -> None:
        self._event = threading.Event()
        self._event.set()

    def pause(self) -> None:
        self._event.clear()

    def resume(self) -> None:
        self._event.set()

    def wait_if_paused(self) -> None:
        self._event.wait()

    @property
    def paused(self) -> bool:
        return not self._event.is_set()
