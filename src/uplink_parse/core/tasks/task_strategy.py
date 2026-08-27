from __future__ import annotations

import asyncio
import inspect
from typing import Any

from src.uplink_parse.core.exceptions import StrategyNotFoundError
from src.uplink_parse.core.utils import to_list
from uplink_parse.core.utils.singleton import get_instance


class BaseTaskStrategy:
    __slots__ = ()

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
        self, target: Any, lst: list[Any], batch_size: int, ut: bool
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
        return inspect.isasyncgenfunction(target)

    async def __call__(
        self, target: Any, lst: list[Any], batch_size: int, ut: bool
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
        return inspect.isgeneratorfunction(target)

    async def __call__(
        self, target: Any, lst: list[Any], batch_size: int, ut: bool
    ) -> None:
        data = await asyncio.to_thread(lambda: list(target())) if ut else list(target())
        self._flush_batch(lst, data)


class _CoroStrategy(BaseTaskStrategy):
    @staticmethod
    def is_supported(target: Any) -> bool:
        return inspect.iscoroutine(target)

    async def __call__(
        self, target: Any, lst: list[Any], batch_size: int, ut: bool
    ) -> None:
        self._flush_batch(lst, [await target])


class _FuncSyncStrategy(BaseTaskStrategy):
    @staticmethod
    def is_supported(target: Any) -> bool:
        return callable(target)

    async def __call__(
        self, target: Any, lst: list[Any], batch_size: int, ut: bool
    ) -> None:
        self._flush_batch(lst, [await asyncio.to_thread(target) if ut else target()])
