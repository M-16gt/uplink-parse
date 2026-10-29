from __future__ import annotations

import asyncio
import inspect
from functools import singledispatch
from typing import Any

from uplink_parse.core.tasks.compat import await_or_return, code_kind
from uplink_parse.core.utils import to_list
from uplink_parse.core.utils.singleton import get_instance


class BaseTaskStrategy:
    """Как выполнить поле и сложить результат в ``lst``.

    Встроенные виды (функция, генератор, корутина, async-генератор) выбираются
    по флагам кода. Свой вид объявляется одной строкой и регистрируется сам,
    порядок объявления ни на что не влияет::

        class GlomStrategy(BaseTaskStrategy, targets=(TType,)):
            async def __call__(self, target, lst, batch_size, use_thread): ...

    Стратегия — без состояния (один экземпляр на класс).
    """

    __slots__ = ()

    # TODO: Переделать, чтобы работало через BaseGeneric с оберткой над config_types
    def __init_subclass__(
        cls, *, targets: tuple[type, ...] = (), **kwargs: Any
    ) -> None:
        super().__init_subclass__(**kwargs)
        for target_type in targets:
            select_strategy.register(
                target_type, lambda _target, cls=cls: get_instance(cls)
            )

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

    async def __call__(
        self, target: Any, lst: list[Any], batch_size: int, use_thread: bool
    ) -> None:
        raise NotImplementedError

    @staticmethod
    def get_strategy(target: Any) -> BaseTaskStrategy:
        return select_strategy(target)


class _FuncAsyncGenStrategy(BaseTaskStrategy):
    async def __call__(
        self, target: Any, lst: list[Any], batch_size: int, use_thread: bool
    ) -> None:
        gen = target()
        batch = []
        async for item in gen:
            batch.append(await await_or_return(item))
            if len(batch) >= batch_size:
                self._flush_batch(lst, batch)
        if batch:
            self._flush_batch(lst, batch)


class _FuncSyncGenStrategy(BaseTaskStrategy):
    async def __call__(
        self, target: Any, lst: list[Any], batch_size: int, use_thread: bool
    ) -> None:
        data = (
            await asyncio.to_thread(lambda: list(target()))
            if use_thread
            else list(target())
        )
        self._flush_batch(lst, [await await_or_return(item) for item in data])


class _FuncAsyncStrategy(BaseTaskStrategy):
    async def __call__(
        self, target: Any, lst: list[Any], batch_size: int, use_thread: bool
    ) -> None:
        self._flush_batch(lst, [await await_or_return(await target())])


class _FuncSyncStrategy(BaseTaskStrategy):
    async def __call__(
        self, target: Any, lst: list[Any], batch_size: int, use_thread: bool
    ) -> None:
        result = await asyncio.to_thread(target) if use_thread else target()
        self._flush_batch(lst, [await await_or_return(result)])


_BY_KIND: dict[int, BaseTaskStrategy] = {
    0: get_instance(_FuncSyncStrategy),
    inspect.CO_GENERATOR: get_instance(_FuncSyncGenStrategy),
    inspect.CO_COROUTINE: get_instance(_FuncAsyncStrategy),
    inspect.CO_ASYNC_GENERATOR: get_instance(_FuncAsyncGenStrategy),
}


@singledispatch
def select_strategy(target: Any) -> BaseTaskStrategy:
    """Стратегия для ``target``: сначала зарегистрированная по типу
    (``targets=`` у подкласса), иначе по виду функции — один lookup."""
    return _BY_KIND.get(code_kind(target), _BY_KIND[0])
