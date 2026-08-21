from typing import Any

from src.uplink_parse.core.processor import BaseProcessor

__all__ = ["fields"]


class _Fields(BaseProcessor[dict[str, Any]]):
    @staticmethod
    def _populate_target(
        result: dict[str, Any], target: dict[str, Any]
    ) -> dict[str, Any]:
        for d in result.values():
            target.update(d)
        return target


fields = _Fields()
