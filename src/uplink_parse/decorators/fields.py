from typing import Any

from uplink_parse.core.processor import BaseProcessor
from uplink_parse.core.utils.singleton import get_instance

__all__ = ["fields"]


class _Fields(BaseProcessor[dict[str, Any]]):
    @staticmethod
    def _populate_target(
        result: dict[str, Any], target: dict[str, Any]
    ) -> dict[str, Any]:
        for d in result.values():
            target.update(d)
        return target


fields = get_instance(_Fields)
