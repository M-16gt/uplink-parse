from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any, ClassVar

from src.uplink_parse.core._dataclasses import FuncMeta
from src.uplink_parse.core.hooks import SKIP, HookSpec
from src.uplink_parse.core.tasks.compat import await_or_return
from src.uplink_parse.core.tasks.task_strategy import BaseTaskStrategy


class TaskRunner:
    __slots__ = ("batch_size", "use_thread_for_sync", "on_error", "hooks")

    default_hooks: ClassVar[HookSpec] = HookSpec()

    def __init__(
        self,
        batch_size: int = 200,
        use_thread_for_sync: bool = True,
        on_error: Callable[[Exception, FuncMeta, list[Any]], None] | None = None,
        hooks: HookSpec | None = None,
    ):
        self.batch_size = batch_size
        self.use_thread_for_sync = use_thread_for_sync
        self.on_error = on_error or self._default_on_error
        self.hooks = hooks if hooks is not None else type(self).default_hooks

    @staticmethod
    def _default_on_error(
        exc: Exception, func_meta: FuncMeta, result_list: list[Any]
    ) -> None:
        raise exc

    async def __call__(self, funcs: list[FuncMeta]) -> dict[str, Any]:
        if not funcs:
            return {}

        results: list[list[Any]] = [[] for _ in funcs]
        skipped_func: list[Any] = []
        tasks = [
            asyncio.create_task(self._run_single(func_meta, results[i], skipped_func))
            for i, func_meta in enumerate(funcs)
        ]

        await asyncio.gather(*tasks, return_exceptions=False)
        return self._unwrap_results(funcs, results, skipped_func)

    async def _run_single(
        self, func_meta: FuncMeta, result_list: list[Any], skipped_func: list[Any]
    ) -> None:
        merged_pre = self.hooks.pre + func_meta.hooks.pre
        merged_post = self.hooks.post + func_meta.hooks.post
        merged_error = self.hooks.error + func_meta.hooks.error

        try:
            pre_res = await self._run_pre(func_meta, merged_pre)
            if pre_res is SKIP:
                skipped_func.append(func_meta)
                return

            if pre_res is True:
                await func_meta.strategy(
                    func_meta.coroutine_or_func,
                    result_list,
                    self.batch_size,
                    self.use_thread_for_sync,
                )
            else:
                BaseTaskStrategy._flush_batch(result_list, [pre_res])

            self._run_post(merged_post, result_list)
        except Exception as exc:
            handled, value = await self._run_error(merged_error, func_meta, exc)
            if not handled:
                self.on_error(exc, func_meta, result_list)
            elif value is not SKIP:
                result_list.append(value)

    @staticmethod
    async def _run_pre(
        func_meta: FuncMeta, merged_pre: list[Callable[..., Any]]
    ) -> Any:
        for h in merged_pre:
            res = await await_or_return(h(func_meta))
            if res is SKIP:
                return SKIP
            if res is not True:
                return res
        return True

    @staticmethod
    def _run_post(
        merged_post: list[Callable[..., Any]], result_list: list[Any]
    ) -> None:
        if not merged_post:
            return
        kept: list[Any] = []
        for item in result_list:
            for h in merged_post:
                item = h(item)
                if item is SKIP:
                    break
            if item is not SKIP:
                kept.append(item)
        result_list[:] = kept

    @staticmethod
    async def _run_error(
        merged_error: list[Callable[..., Any]], func_meta: FuncMeta, exc: Exception
    ) -> tuple[bool, Any]:
        for h in merged_error:
            try:
                return True, await await_or_return(h(exc, func_meta))
            except Exception:
                continue
        return False, None

    @staticmethod
    def _unwrap_results(
        funcs: list[FuncMeta], results: list[list[Any]], skipped_func: list[Any]
    ) -> dict[str, Any]:
        target: dict[str, Any] = {}
        for func_meta, result in zip(funcs, results, strict=False):
            if func_meta not in skipped_func:
                target[func_meta.name] = result[0] if len(result) == 1 else result
        return target
