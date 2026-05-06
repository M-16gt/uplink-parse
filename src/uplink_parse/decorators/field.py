from typing import Any

from uplink_parse.core.processor import BaseProcessor

__all__ = ["field"]


class _Field(BaseProcessor[Any, dict]):
    @staticmethod
    def _populate_target(
            owner: Any,
            func_names: set[str],
            target: dict
    ) -> dict:
        target.update({func_name: getattr(owner, func_name)() for func_name in func_names})

        return target


field = _Field()
