import asyncio
from collections.abc import Callable
from typing import Any

from src.uplink_parse.core._dataclasses import FuncMeta


class TaskRunner:
    __slots__ = ("batch_size", "use_thread_for_sync", "on_error")

    def __init__(
        self,
        batch_size: int = 200,
        use_thread_for_sync: bool = True,
        on_error: Callable[[Exception, FuncMeta, list[Any]], None] | None = None,
    ):
        self.batch_size = batch_size
        self.use_thread_for_sync = use_thread_for_sync
        self.on_error = on_error or self._default_on_error

    @staticmethod
    def _default_on_error(
        exc: Exception, func_meta: FuncMeta, result_list: list[Any]
    ) -> None:
        raise

    async def __call__(self, funcs: list[FuncMeta]) -> dict[str, Any]:
        if not funcs:
            return {}

        results: list[list[Any]] = [[] for _ in funcs]
        tasks = [
            asyncio.create_task(self._run_single(func_meta, results[i]))
            for i, func_meta in enumerate(funcs)
        ]

        await asyncio.gather(*tasks, return_exceptions=False)
        return self._unwrap_results(funcs, results)

    async def _run_single(self, func_meta: FuncMeta, result_list: list[Any]) -> None:
        try:
            await func_meta.strategy(
                func_meta.coroutine_or_func,
                result_list,
                self.batch_size,
                self.use_thread_for_sync,
            )
        except Exception as exc:
            self.on_error(exc, func_meta, result_list)

    @staticmethod
    def _unwrap_results(
        funcs: list[FuncMeta], results: list[list[Any]]
    ) -> dict[str, Any]:
        target: dict[str, Any] = {}
        for func_meta, result in zip(funcs, results, strict=False):
            target[func_meta.name] = result[0] if len(result) == 1 else result
        return target
