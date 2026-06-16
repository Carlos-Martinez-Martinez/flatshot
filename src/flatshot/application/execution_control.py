"""Qt-free pause and cancellation primitives for background jobs."""
from __future__ import annotations

import logging
import threading

_logger = logging.getLogger(__name__)


class CancellationToken:
    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    def reset(self) -> None:
        self._event.clear()

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

    def wait_if_paused(self, timeout: float = 30.0) -> None:
        if not self._event.wait(timeout=timeout):
            _logger.warning("PauseToken.wait_if_paused timed out after %.1fs", timeout)

    @property
    def paused(self) -> bool:
        return not self._event.is_set()
