from __future__ import annotations

from typing import Any

from src.uplink_parse.core.singleton import Singleton


class ResponseAccessor(Singleton):
    @staticmethod
    def _get(response: Any, attr: str) -> Any:
        if not hasattr(response, attr):
            raise AttributeError(
                f"Response {type(response).__qualname__} has no attribute '{attr}'"
            )

        value = getattr(response, attr)

        return value() if callable(value) else value

    @staticmethod
    def get_any(response: Any, *attrs: str) -> Any:
        for attr in attrs:
            if hasattr(response, attr):
                return ResponseAccessor._get(response, attr)

        raise AttributeError(
            f"Response {type(response).__qualname__} has none of "
            f"the attributes: {attrs}"
        )
