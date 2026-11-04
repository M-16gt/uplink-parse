from __future__ import annotations

import asyncio
from collections.abc import Mapping
from functools import partial
from itertools import islice
from typing import Any

from uplink_parse.core.utils import await_or_return
from uplink_parse.decorators.hooks import SKIP, UNHANDLED
from uplink_parse.decorators.meta import FuncMeta, HookPoint, HookSpec, PopulateFunc


async def _gather(coros: list[Any]) -> list[Any]:
    if len(coros) == 1:
        return [await coros[0]]
    loop = asyncio.get_running_loop()
    return list(
        await asyncio.gather(
            *[asyncio.Task(c, loop=loop, eager_start=True) for c in coros]
        )
    )


class TaskRunner:
    """Уровень 3: выполняет поля парсера и собирает из них итоговый словарь.

    Вход — ``__call__(groups)``, где ``groups`` — поля, сгруппированные по
    ``populate``.

    Поля видят ``ctx`` (``self.response`` и т.д.) только потому, что
    ``asyncio.gather`` оборачивает корутины в задачи, а задача копирует
    текущий ``contextvars``-контекст; sync-поля в потоках — потому что
    ``asyncio.to_thread`` делает то же самое. Запускать поля иначе
    (``loop.run_in_executor``, ``threading.Thread``) нельзя без
    ``contextvars.copy_context().run`` — ``ctx`` в них пропадёт.

    Хуки поля собираются один раз, при его первом запуске.
    """

    def __init__(
        self,
        batch_size: int = 200,
        use_thread_for_sync: bool = True,
        class_hooks: tuple[HookSpec, ...] = (),
    ) -> None:
        self.batch_size = batch_size
        self.use_thread_for_sync = use_thread_for_sync
        self.class_hooks = class_hooks
        self._plans: dict[FuncMeta, tuple[tuple[Any, ...], ...]] = {}

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

    def _plan(self, meta: FuncMeta) -> tuple[tuple[Any, ...], ...]:
        """``(pre, params, post, error)`` — все хуки поля в порядке вызова."""
        plan = self._plans.get(meta)
        if plan is None:
            plan = self._plans[meta] = tuple(
                self._hooks(point, meta)
                for point in (
                    HookPoint.PRE,
                    HookPoint.PARAMS,
                    HookPoint.POST,
                    HookPoint.ERROR,
                )
            )
        return plan

    async def _run_field(self, meta: FuncMeta) -> Any:
        pre, params, post, error = self._plan(meta)
        try:
            decision: Any = True
            for hook in pre:
                decision = await await_or_return(hook(meta))
                if decision is not True:
                    break
            if decision is SKIP:
                return SKIP

            if decision is True:
                kwargs: dict[str, Any] = {}
                for hook in params:
                    hook_params = await await_or_return(hook(meta))
                    if not isinstance(hook_params, Mapping):
                        raise TypeError("paramshook must return a mapping")
                    kwargs.update(hook_params)
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

            for hook in post:
                value = await await_or_return(hook(value, meta))
                if value is SKIP:
                    break
            return value
        except Exception as exc:
            for hook in error:
                value = await await_or_return(hook(exc, meta))
                if value is not UNHANDLED:
                    return value
            raise

    async def __call__(
        self, groups: Mapping[PopulateFunc, list[FuncMeta]]
    ) -> dict[str, Any]:
        metas = [meta for group in groups.values() for meta in group]
        values = iter(await _gather([self._run_field(meta) for meta in metas]))
        target: dict[str, Any] = {}
        for populate, group in groups.items():
            result = {
                meta.name: value
                for meta, value in zip(group, islice(values, len(group)), strict=True)
                if value is not SKIP
            }
            target = populate(result, target)
        return target
