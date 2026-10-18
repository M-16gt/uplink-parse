from __future__ import annotations

from typing import Any


class ResponseAccessor:
    @staticmethod
    def _get(response: Any, attr: str) -> Any:
        return value() if callable(value := getattr(response, attr)) else value

    @staticmethod
    def get_any(response: Any, *attrs: str) -> Any:
        for attr in attrs:
            if hasattr(response, attr):
                return ResponseAccessor._get(response, attr)

        raise AttributeError(
            f"Response {type(response).__qualname__} has none of "
            f"the attributes: {attrs}"
        )
