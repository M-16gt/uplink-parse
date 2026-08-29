from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import attrs

from uplink_parse.core.hooks import HookSpec
from uplink_parse.core.utils import transpose_dict_to_dataclass

if TYPE_CHECKING:
    from uplink_parse.core.tasks.task_runner import TaskRunner


@attrs.frozen
class FuncMeta:
    name: str
    func: Callable[..., Any]
    strategy: Callable[..., Any]
    hooks: HookSpec = attrs.field(factory=HookSpec)


@attrs.frozen
class FuncsMeta:
    funcs: list[FuncMeta] = attrs.field(factory=list)

    @classmethod
    def build(
        cls,
        base: type,
        owner: type | None = None,
        extractors: Any | None = None,
        **kwargs: Any,
    ) -> FuncsMeta:
        if extractors is None:
            from uplink_parse.core.extractors import ExtractorChain

            extractors = ExtractorChain()
        return cls(
            funcs=transpose_dict_to_dataclass(
                extractors.run(owner, base, **kwargs),
                FuncMeta,
            )
        )

    def is_empty(self) -> bool:
        return not self.funcs


@attrs.define
class _ParseMeta:
    funcs: dict[type, FuncsMeta] = attrs.field(factory=dict)

    def is_empty(self) -> bool:
        return not self.funcs

    @classmethod
    def build(
        cls,
        owner: Any,
        **kwargs: Any,
    ) -> _ParseMeta:
        return cls(
            {
                processor_cls: FuncsMeta.build(processor_cls, owner, **kwargs)
                for processor_cls in owner.parse_fields
            }
        )


@attrs.define(slots=False)
class ScraperCtxData:
    response: Any | None = None
    response_raw: Any | None = None
    consumer: Any | None = None
    scraper: Any | None = None
    request: Any | None = None


@attrs.define(slots=False)
class Storage:
    parse_funcs_meta: _ParseMeta
    task_runner: TaskRunner
    strategy_params: dict[str, Any] = attrs.field(factory=dict)
