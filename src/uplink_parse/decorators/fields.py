from typing import Any

from uplink_parse.core.processor import processor

__all__ = ["fields"]


def _populate(result: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    for d in result.values():
        target.update(d)
    return target


fields = processor(_populate)
