from __future__ import annotations

import functools
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

import attrs

from src.uplink_parse.core._extractors import (
    _extract_coroutine_or_func,
    _extract_name,
    _extract_strategy,
    _extract_url,
)
from src.uplink_parse.core.utils import _transpose_dict_to_dataclass

if TYPE_CHECKING:
    from uplink_parse.core.tasks.task_runner import TaskRunner


@attrs.define
class FuncMeta:
    name: str
    url: Callable[..., Any]
    coroutine_or_func: Callable[..., Any] | Awaitable[Any]
    strategy: Callable[..., Any]


@attrs.define
class _ParseMeta:
    funcs: list[FuncMeta] = attrs.field(factory=list)

    def is_nan_obj(self) -> bool:
        return not self.funcs

    @classmethod
    def from_extractors(
        cls,
        base: type,
        owner: type | None = None,
        extractors: list[Callable[..., Any]] | None = None,
        **kwargs: Any,
    ) -> _ParseMeta:
        if extractors is None:
            extractors = [
                _extract_name,
                _extract_url,
                _extract_coroutine_or_func,
                _extract_strategy,
            ]
        return cls(
            funcs=_transpose_dict_to_dataclass(
                functools.reduce(
                    lambda acc, fn: {**acc, **fn(owner, base, acc, kwargs)},
                    extractors,
                    {},
                ),
                FuncMeta,
            )
        )


@attrs.define(slots=False)
class ScraperCtxData:
    response: Any | None = None
    request: Any | None = None
    consumer: Any | None = None
    scraper: Any | None = None
    builder: Any | None = None


@attrs.define(slots=False)
class Storage:
    parse_funcs_meta: dict[str, _ParseMeta]
    task_runner: TaskRunner
    strategy_params: dict[str, Any] = attrs.field(factory=dict)
