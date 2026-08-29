from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import attrs

from uplink_parse.core.hooks import HookSpec
from uplink_parse.core.utils import transpose_dict_to_dataclass

if TYPE_CHECKING:
    from uplink_parse.core.tasks.task_runner import TaskRunner


class _SizedMeta:
    __slots__ = ()

    def __len__(self) -> int:
        raise NotImplementedError

    def __bool__(self) -> bool:
        return bool(len(self))

    def is_empty(self) -> bool:
        return not self


@attrs.frozen
class FuncMeta:
    name: str
    func: Callable[..., Any]
    strategy: Callable[..., Any]
    hooks: HookSpec = attrs.field(factory=HookSpec)


@attrs.frozen
class FuncsMeta(_SizedMeta):
    funcs: list[FuncMeta] = attrs.field(factory=list)

    def __len__(self) -> int:
        return len(self.funcs)

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


@attrs.frozen
class _ParseMeta(_SizedMeta):
    by_processor: dict[type, FuncsMeta] = attrs.field(factory=dict)

    def __len__(self) -> int:
        return len(self.by_processor)

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
