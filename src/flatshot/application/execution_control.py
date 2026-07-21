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

    def wait_if_paused(
        self,
        timeout: float | None = 30.0,
        cancellation_token: CancellationToken | None = None,
    ) -> bool:
        """Wait for resume, returning whether cancellation was observed.

        The bounded timeout remains available for diagnostics and backwards
        compatibility. Export execution passes ``timeout=None`` so a paused
        job cannot silently continue with incomplete work.
        """
        if not self.paused:
            return bool(cancellation_token and cancellation_token.cancelled)

        if timeout is not None:
            if self._event.wait(timeout=timeout):
                return bool(cancellation_token and cancellation_token.cancelled)
            _logger.warning("PauseToken.wait_if_paused timed out after %.1fs", timeout)
            return bool(cancellation_token and cancellation_token.cancelled)

        while not self._event.wait(timeout=0.1):
            if cancellation_token and cancellation_token.cancelled:
                return True
        return bool(cancellation_token and cancellation_token.cancelled)

    @property
    def paused(self) -> bool:
        return not self._event.is_set()
