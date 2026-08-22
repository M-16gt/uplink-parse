from __future__ import annotations

import asyncio
import inspect
from typing import Any

from src.uplink_parse.core.cached import Cached
from src.uplink_parse.core.exceptions import StrategyNotFoundError
from src.uplink_parse.core.utils import to_list


class BaseTaskStrategy(Cached):
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
    def is_supported(tgt: Any) -> bool:
        raise NotImplementedError

    async def __call__(self, tgt: Any, lst: list[Any], bs: int, ut: bool) -> None:
        raise NotImplementedError

    @classmethod
    def get_strategy(cls, tgt: Any) -> object:
        for strategy in cls.__subclasses__():
            if strategy.is_supported(tgt):
                return strategy()
        raise StrategyNotFoundError(
            f"No BaseTaskStrategy subclass supports target {tgt!r}.",
            details={"target": tgt},
            source=cls.__name__,
        )


class _FuncAsyncGenStrategy(BaseTaskStrategy):
    @staticmethod
    def is_supported(tgt: Any) -> bool:
        return inspect.isasyncgenfunction(tgt)

    async def __call__(self, tgt: Any, lst: list[Any], bs: int, ut: bool) -> None:
        gen = tgt()
        batch = []
        async for item in gen:
            batch.append(item)
            if len(batch) >= bs:
                self._flush_batch(lst, batch)
        if batch:
            self._flush_batch(lst, batch)


class _FuncSyncGenStrategy(BaseTaskStrategy):
    @staticmethod
    def is_supported(tgt: Any) -> bool:
        return inspect.isgeneratorfunction(tgt)

    async def __call__(self, tgt: Any, lst: list[Any], bs: int, ut: bool) -> None:
        data = await asyncio.to_thread(lambda: list(tgt())) if ut else list(tgt())
        self._flush_batch(lst, data)


class _CoroStrategy(BaseTaskStrategy):
    @staticmethod
    def is_supported(tgt: Any) -> bool:
        return inspect.iscoroutine(tgt)

    async def __call__(self, tgt: Any, lst: list[Any], bs: int, ut: bool) -> None:
        self._flush_batch(lst, [await tgt])


class _FuncSyncStrategy(BaseTaskStrategy):
    @staticmethod
    def is_supported(tgt: Any) -> bool:
        return callable(tgt)

    async def __call__(self, tgt: Any, lst: list[Any], bs: int, ut: bool) -> None:
        self._flush_batch(lst, [await asyncio.to_thread(tgt) if ut else tgt()])
