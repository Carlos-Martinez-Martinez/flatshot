"""Controlled bridge errors for service and HTTP responses."""
from __future__ import annotations


class BridgeError(Exception):
    def __init__(self, code: str, message: str, *, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


class InvalidRequestError(BridgeError):
    def __init__(self, message: str) -> None:
        super().__init__("invalid_request", message, status=400)


class NotFoundError(BridgeError):
    def __init__(self, message: str = "Endpoint not found.") -> None:
        super().__init__("not_found", message, status=404)


class MethodNotAllowedError(BridgeError):
    def __init__(self, message: str = "Method not allowed.") -> None:
        super().__init__("method_not_allowed", message, status=405)


def error_response(error: BridgeError | Exception) -> dict:
    if isinstance(error, BridgeError):
        return {
            "ok": False,
            "error": {
                "code": error.code,
                "message": error.message,
            },
        }
    return {
        "ok": False,
        "error": {
            "code": "internal_error",
            "message": "Internal bridge error.",
        },
    }
