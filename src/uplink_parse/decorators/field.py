from typing import Any

from src.uplink_parse.core.processor import BaseProcessor
from uplink_parse.core.utils.singleton import get_instance

__all__ = ["field"]


class _Field(BaseProcessor[Any]):
    @staticmethod
    def _populate_target(
        result: dict[str, Any], target: dict[str, Any]
    ) -> dict[str, Any]:
        target.update(result)
        return target


field = get_instance(_Field)
