from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

import attrs

from uplink_parse.core.hooks import HookSpec
from uplink_parse.core.utils import transpose_dict_to_dataclass

if TYPE_CHECKING:
    from uplink_parse.core.tasks.task_runner import TaskRunner


@attrs.define
class FuncMeta:
    name: str
    url: Callable[..., Any]
    coroutine_or_func: Callable[..., Any] | Awaitable[Any]
    strategy: Callable[..., Any]
    hooks: HookSpec = attrs.field(factory=HookSpec)


@attrs.define
class _ParseMeta:
    funcs: list[FuncMeta] = attrs.field(factory=list)

    def is_nan_obj(self) -> bool:
        return not self.funcs

    @classmethod
    def build_all(
        cls,
        owner: Any,
        **kwargs: Any,
    ) -> dict[type[Any], _ParseMeta]:

        return {
            processor_cls: cls.from_extractors(processor_cls, owner, **kwargs)
            for processor_cls in owner.parse_fields
        }

    @classmethod
    def from_extractors(
        cls,
        base: type,
        owner: type | None = None,
        extractors: Any | None = None,
        **kwargs: Any,
    ) -> _ParseMeta:
        if extractors is None:
            from uplink_parse.core.extractors import ExtractorChain

            extractors = ExtractorChain()
        return cls(
            funcs=transpose_dict_to_dataclass(
                extractors.run(owner, base, **kwargs),
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
    parse_funcs_meta: dict[type, _ParseMeta]
    task_runner: TaskRunner
    strategy_params: dict[str, Any] = attrs.field(factory=dict)
