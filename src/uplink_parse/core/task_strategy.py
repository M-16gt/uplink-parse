import asyncio
import inspect
from uplink_parse.core.singleton import Singleton
from uplink_parse.core.exceptions import StrategyNotFoundError
from typing import Any


class BaseTaskStrategy(Singleton):

    @staticmethod
    def _flush_batch(lst: list, batch: list) -> None:
        for item in batch:
            if isinstance(item, dict) and len(item) == 1:
                _, val = next(iter(item.items()))
                if isinstance(val, list):
                    lst.extend(val)
                    continue
            if isinstance(item, list):
                lst.extend(item)
            else:
                lst.append(item)
        batch.clear()

    @staticmethod
    def is_supported(tgt: Any) -> bool:
        raise NotImplementedError

    async def __call__(self, tgt: Any, lst: list, bs: int, ut: bool) -> None:
        raise NotImplementedError

    @classmethod
    def get_strategy(cls, tgt: Any) -> "BaseTaskStrategy":
        for strategy in cls.__subclasses__():
            if strategy.is_supported(tgt):
                return strategy()
        raise StrategyNotFoundError(
            f"No BaseTaskStrategy subclass supports target {tgt!r}.",
            target=tgt,
            source=cls.__name__,
        )


class _FuncAsyncGenStrategy(BaseTaskStrategy):
    @staticmethod
    def is_supported(tgt: Any) -> bool:
        return inspect.isasyncgenfunction(tgt)

    async def __call__(self, tgt, lst, bs, ut):
        gen = tgt()
        batch = []
        async for item in gen:
            batch.append(item)
            if len(batch) >= bs: self._flush_batch(lst, batch)
        if batch: self._flush_batch(lst, batch)


class _FuncSyncGenStrategy(BaseTaskStrategy):
    @staticmethod
    def is_supported(tgt: Any) -> bool:
        return inspect.isgeneratorfunction(tgt)

    async def __call__(self, tgt, lst, bs, ut):
        items = list(tgt())
        if not items: return
        data = await asyncio.to_thread(lambda: items) if ut else items
        self._flush_batch(lst, data)


class _CoroStrategy(BaseTaskStrategy):
    @staticmethod
    def is_supported(tgt: Any) -> bool:
        return inspect.iscoroutine(tgt)

    async def __call__(self, tgt, lst, bs, ut):
        self._flush_batch(lst, [await tgt])


class _FuncSyncStrategy(BaseTaskStrategy):
    @staticmethod
    def is_supported(tgt: Any) -> bool:
        return callable(tgt)

    async def __call__(self, tgt, lst, bs, ut):
        self._flush_batch(lst, [await asyncio.to_thread(tgt) if ut else tgt()])


class _UnknownStrategy(BaseTaskStrategy):
    @staticmethod
    def is_supported(tgt: Any) -> bool:
        return True

    async def __call__(self, tgt, lst, bs, ut):
        lst.append(tgt)