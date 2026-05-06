from typing import Any

from uplink_parse.core.processor import BaseProcessor

__all__ = ["fields"]


class _Fields(BaseProcessor[dict, dict]):
    @staticmethod
    def _populate_target(
            owner: Any,
            func_names: set[str],
            target: dict
    ) -> dict:
        for func_name in func_names:
            target.update(getattr(owner, func_name)())

        return target


fields = _Fields()
