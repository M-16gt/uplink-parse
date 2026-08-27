# core/extractors.py
from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from uplink_parse.core.tasks.compat import to_runnable
from uplink_parse.core.tasks.task_strategy import BaseTaskStrategy


class ExtractorChain:
    def steps(self) -> list[tuple[str, Callable[..., Any]]]:
        return [
            ("name", self.extract_name),
            ("url", self.extract_url),
            ("coroutine_or_func", self.extract_coroutine_or_func),
            ("strategy", self.extract_strategy),
        ]

    @staticmethod
    def extract_name(
        owner: Any, base: Any, acc: dict[str, Any], kwargs: dict[str, Any]
    ) -> list[str]:
        return list(base.get_registered(owner.__class__, **kwargs))

    @staticmethod
    def extract_url(
        owner: Any, base: Any, acc: dict[str, Any], kwargs: dict[str, Any]
    ) -> list[Callable[..., Any]]:
        return [getattr(owner, n) for n in acc["name"]]

    @staticmethod
    def extract_coroutine_or_func(
        owner: Any, base: Any, acc: dict[str, Any], kwargs: dict[str, Any]
    ) -> list[Any]:
        return cast(list[Any], to_runnable(*acc["url"]))

    @staticmethod
    def extract_strategy(
        owner: Any, base: Any, acc: dict[str, Any], kwargs: dict[str, Any]
    ) -> list[Any]:
        return [BaseTaskStrategy.get_strategy(c) for c in acc["coroutine_or_func"]]

    def run(self, owner: Any, base: Any, **kwargs: Any) -> dict[str, list[Any]]:
        acc: dict[str, Any] = {}
        for field_name, extractor in self.steps():
            acc[field_name] = extractor(owner, base, acc, kwargs)
        return acc
