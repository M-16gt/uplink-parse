from typing import Any

from uplink_parse.core.processor import BaseProcessor

__all__ = ["field"]


class _Field(BaseProcessor[Any]):
    @staticmethod
    def _populate_target(
            result: dict[str, Any],
            target: dict
    ) -> dict:
        target.update(result)
        return target

field = _Field()
