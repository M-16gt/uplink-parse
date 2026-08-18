from typing import Any

from uplink_parse.core.processor import BaseProcessor

__all__ = ["fields"]


class _Fields(BaseProcessor[dict]):
    @staticmethod
    def _populate_target(
            result: dict[str, Any],
            target: dict
    ) -> dict:
        for d in result.values():
            target.update(d)
        return target


fields = _Fields()
