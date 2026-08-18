from __future__ import annotations
from collections import defaultdict

import attrs
from typing import Callable, Awaitable, Any

@attrs.define
class FuncMeta:
    name: str
    url: Callable
    coroutine_or_func: Callable | Awaitable
    strategy: Callable


@attrs.define
class _ParseMeta:
    funcs: list[FuncMeta] = attrs.field(factory=list)

    def is_nan_obj(self):
        return not self.funcs

@attrs.define(slots=False)
class ScraperCtxData:
    response: Any | None = None
    request: Any | None = None
    consumer: Any | None = None
    scraper: Any | None = None
    builder: Any | None = None

@attrs.define(slots=False)
class Storage:
    parse_funcs_meta: defaultdict[str, _ParseMeta]
    task_runner: "TaskRunner"