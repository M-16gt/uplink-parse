from __future__ import annotations

import asyncio
from typing import Any

from uplink_parse.core.exceptions import StrategyNotFoundError
from uplink_parse.core.tasks.compat import (
    await_or_return,
    isasyncgenfunction,
    iscoroutinefunction,
    isgeneratorfunction,
)
from uplink_parse.core.utils import to_list
from uplink_parse.core.utils.singleton import get_instance


class BaseTaskStrategy:
    slots = ()

    @staticmethod
    def _flush_batch(lst: list[Any], batch: list[Any]) -> None:
        for item in batch:
            if isinstance(item, dict) and len(item) == 1:
                _, val = next(iter(item.items()))
                if isinstance(val, list):
                    lst.extend(val)
                    continue
            lst.extend(to_list(item))
        batch.clear()

    @staticmethod
    def is_supported(target: Any) -> bool:
        raise NotImplementedError

    async def __call__(
        self, target: Any, lst: list[Any], batch_size: int, use_thread: bool
    ) -> None:
        raise NotImplementedError

    @classmethod
    def get_strategy(cls, target: Any) -> object:
        for strategy in cls.__subclasses__():
            if strategy.is_supported(target):
                return get_instance(strategy)
        raise StrategyNotFoundError(
            f"No BaseTaskStrategy subclass supports target {target!r}.",
            details={"target": target},
            source=cls.__name__,
        )


class _FuncAsyncGenStrategy(BaseTaskStrategy):
    @staticmethod
    def is_supported(target: Any) -> bool:
        return isasyncgenfunction(target)

    async def __call__(
        self, target: Any, lst: list[Any], batch_size: int, use_thread: bool
    ) -> None:
        gen = target()
        batch = []
        async for item in gen:
            batch.append(item)
            if len(batch) >= batch_size:
                self._flush_batch(lst, batch)
        if batch:
            self._flush_batch(lst, batch)


class _FuncSyncGenStrategy(BaseTaskStrategy):
    @staticmethod
    def is_supported(target: Any) -> bool:
        return isgeneratorfunction(target)

    async def __call__(
        self, target: Any, lst: list[Any], batch_size: int, use_thread: bool
    ) -> None:
        data = (
            await asyncio.to_thread(lambda: list(target()))
            if use_thread
            else list(target())
        )
        self._flush_batch(lst, data)


class _CallableStrategy(BaseTaskStrategy):
    @staticmethod
    def is_supported(target: Any) -> bool:
        return callable(target)

    async def __call__(
        self, target: Any, lst: list[Any], batch_size: int, use_thread: bool
    ) -> None:
        if use_thread and not iscoroutinefunction(target):
            result = await asyncio.to_thread(target)
        else:
            result = target()
        result = await await_or_return(result)
        self._flush_batch(lst, [result])
