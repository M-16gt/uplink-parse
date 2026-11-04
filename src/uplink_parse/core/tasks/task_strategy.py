from __future__ import annotations

import asyncio
import functools
import inspect
from functools import singledispatch
from typing import Any, ClassVar

from uplink_parse.core.utils.singleton import get_instance


class BaseTaskStrategy:
    """Как выполнить поле и сложить результат в ``lst``.

    Результат поля берётся из ``lst``: ровно один элемент — это и есть значение
    поля, иначе значение — весь список. Стратегия-поток (``stream = True``)
    всегда отдаёт список, даже из одного элемента или пустой.

    Встроенные виды (функция, генератор, корутина, async-генератор) выбираются
    по флагам кода. Свой вид объявляется одной строкой и регистрируется сам,
    порядок объявления ни на что не влияет::

        class GlomStrategy(BaseTaskStrategy, targets=(TType,)):
            async def __call__(self, target, lst, batch_size, use_thread): ...

    Стратегия — без состояния (один экземпляр на класс).
    """

    __slots__ = ()

    #: ``True`` — поле выдаёт поток значений (генератор) и его результат всегда
    #: список; ``False`` — одно значение, которое поле возвращает как есть.
    stream: ClassVar[bool] = False

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
        """Сложить ``batch`` (элементы потока) в ``lst``: списки и кортежи —
        поэлементно, ``None`` — пропустить, ``{ключ: список}`` — развернуть.

        Горячий путь (по разу на каждый элемент генератора), поэтому без
        вспомогательных вызовов. По той же причине стратегии ниже проверяют
        ``hasattr(x, "__await__")`` на месте, а не через ``await_or_return``:
        каждый его вызов создаёт корутину.
        """
        for item in batch:
            if isinstance(item, (list, tuple)):
                lst.extend(item)
            elif item is None:
                continue
            elif (
                isinstance(item, dict)
                and len(item) == 1
                and isinstance(val := next(iter(item.values())), list)
            ):
                lst.extend(val)
            else:
                lst.append(item)
        batch.clear()

    async def __call__(
        self, target: Any, lst: list[Any], batch_size: int, use_thread: bool
    ) -> None:
        raise NotImplementedError

    @staticmethod
    def get_strategy(target: Any) -> BaseTaskStrategy:
        return select_strategy(target)


class _FuncAsyncGenStrategy(BaseTaskStrategy):
    stream = True

    async def __call__(
        self, target: Any, lst: list[Any], batch_size: int, use_thread: bool
    ) -> None:
        batch = []
        async for item in target():
            if hasattr(item, "__await__"):
                item = await item
            batch.append(item)
            if len(batch) >= batch_size:
                self._flush_batch(lst, batch)
        if batch:
            self._flush_batch(lst, batch)


class _FuncSyncGenStrategy(BaseTaskStrategy):
    stream = True

    async def __call__(
        self, target: Any, lst: list[Any], batch_size: int, use_thread: bool
    ) -> None:
        data = (
            await asyncio.to_thread(lambda: list(target()))
            if use_thread
            else list(target())
        )
        self._flush_batch(
            lst, [await x if hasattr(x, "__await__") else x for x in data]
        )


class _FuncAsyncStrategy(BaseTaskStrategy):
    async def __call__(
        self, target: Any, lst: list[Any], batch_size: int, use_thread: bool
    ) -> None:
        result = await target()
        if hasattr(result, "__await__"):
            result = await result
        lst.append(result)


class _FuncSyncStrategy(BaseTaskStrategy):
    async def __call__(
        self, target: Any, lst: list[Any], batch_size: int, use_thread: bool
    ) -> None:
        result = await asyncio.to_thread(target) if use_thread else target()
        if hasattr(result, "__await__"):
            result = await result
        lst.append(result)


#: Флаги кода, определяющие вид функции. Взаимоисключающие: у функции
#: выставлен не больше одного, поэтому вид — это просто ``flags & маска``.
_KIND_MASK = inspect.CO_GENERATOR | inspect.CO_COROUTINE | inspect.CO_ASYNC_GENERATOR


def code_kind(func: Any) -> int:
    """Вид функции одним числом: ``0`` (обычная) или один из флагов
    ``CO_GENERATOR`` / ``CO_COROUTINE`` / ``CO_ASYNC_GENERATOR``.
    Для объектов без кода (вызываемые классы и т.п.) — ``0``."""
    func = getattr(func, "__func__", func)
    while isinstance(func, functools.partial):
        func = func.func
    code = getattr(func, "__code__", None)
    return (code.co_flags if code is not None else 0) & _KIND_MASK


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
