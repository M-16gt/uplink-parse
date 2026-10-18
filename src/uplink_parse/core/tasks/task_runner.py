from __future__ import annotations

import asyncio
from collections.abc import Iterable, Mapping
from functools import partial
from typing import Any

from uplink_parse.core._dataclasses import FuncMeta, HookPoint, HookSpec
from uplink_parse.core.hooks import SKIP, UNHANDLED
from uplink_parse.core.tasks.compat import await_or_return


class TaskRunner:
    def __init__(
        self,
        batch_size: int = 200,
        use_thread_for_sync: bool = True,
        class_hooks: tuple[HookSpec, ...] = (),
    ) -> None:
        self.batch_size = batch_size
        self.use_thread_for_sync = use_thread_for_sync
        self.class_hooks = class_hooks

    def _hooks(self, point: HookPoint, meta: FuncMeta) -> tuple[Any, ...]:
        if point in (HookPoint.POST, HookPoint.ERROR):
            return (
                *meta.hooks.of(point),
                *(h for spec in reversed(self.class_hooks) for h in spec.of(point)),
            )
        return (
            *(h for spec in self.class_hooks for h in spec.of(point)),
            *meta.hooks.of(point),
        )

    async def _run_field(self, meta: FuncMeta) -> Any:
        try:
            decision: Any = True
            for hook in self._hooks(HookPoint.PRE, meta):
                decision = await await_or_return(hook(meta))
                if decision is not True:
                    break
            if decision is SKIP:
                return SKIP

            if decision is True:
                kwargs: dict[str, Any] = {}
                for hook in self._hooks(HookPoint.PARAMS, meta):
                    params = await await_or_return(hook(meta))
                    if not isinstance(params, Mapping):
                        raise TypeError("paramshook must return a mapping")
                    kwargs.update(params)
                items: list[Any] = []
                await meta.strategy(
                    partial(meta.func, **kwargs),
                    items,
                    self.batch_size,
                    self.use_thread_for_sync,
                )
                value = items[0] if len(items) == 1 else items
            else:
                value = decision

            for hook in self._hooks(HookPoint.POST, meta):
                value = await await_or_return(hook(value, meta))
                if value is SKIP:
                    break
            return value
        except Exception as exc:
            for hook in self._hooks(HookPoint.ERROR, meta):
                value = await await_or_return(hook(exc, meta))
                if value is not UNHANDLED:
                    return value
            raise

    async def __call__(self, funcs: Iterable[FuncMeta]) -> dict[str, Any]:
        metas = list(funcs)
        values = await asyncio.gather(*(self._run_field(meta) for meta in metas))
        return {
            meta.name: value
            for meta, value in zip(metas, values, strict=True)
            if value is not SKIP
        }
