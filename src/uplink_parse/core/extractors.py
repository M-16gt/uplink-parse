from collections.abc import Callable
from typing import Any

from uplink_parse.core.hooks import HookSpec
from uplink_parse.core.tasks.task_strategy import BaseTaskStrategy
from uplink_parse.core.utils.markers import Markers


class ExtractorChain:
    def steps(self) -> list[tuple[str, Callable[..., Any]]]:
        return [
            ("name", self.extract_name),
            ("func", self.extract_func),
            ("hooks", self.extract_hooks),
            ("strategy", self.extract_strategy),
        ]

    @staticmethod
    def extract_hooks(
        owner: Any, base: Any, acc: dict[str, Any], kwargs: dict[str, Any]
    ) -> list[HookSpec]:
        return [getattr(f, Markers.HOOKS, HookSpec()) for f in acc["func"]]

    @staticmethod
    def extract_name(
        owner: Any, base: Any, acc: dict[str, Any], kwargs: dict[str, Any]
    ) -> list[str]:
        return list(owner.parse_fields.get(base, []))

    @staticmethod
    def extract_func(
        owner: Any, base: Any, acc: dict[str, Any], kwargs: dict[str, Any]
    ) -> list[Callable[..., Any]]:
        return [getattr(owner, n) for n in acc["name"]]

    @staticmethod
    def extract_strategy(
        owner: Any, base: Any, acc: dict[str, Any], kwargs: dict[str, Any]
    ) -> list[Any]:
        return [BaseTaskStrategy.get_strategy(c) for c in acc["func"]]

    def run(self, owner: Any, base: Any, **kwargs: Any) -> dict[str, list[Any]]:
        acc: dict[str, Any] = {}
        for field_name, extractor in self.steps():
            acc[field_name] = extractor(owner, base, acc, kwargs)
        return acc
