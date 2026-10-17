from typing import Any

from uplink_parse.core.processor import processor

__all__ = ["field"]


def _populate(result: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    target.update(result)
    return target


field = processor(_populate)
