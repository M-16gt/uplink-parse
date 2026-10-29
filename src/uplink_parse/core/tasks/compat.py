from __future__ import annotations

import functools
import inspect
from typing import Any

#: Флаги кода, определяющие вид функции. Взаимоисключающие: у функции
#: выставлен не больше одного, поэтому вид — это просто ``flags & маска``.
_KIND_MASK = inspect.CO_GENERATOR | inspect.CO_COROUTINE | inspect.CO_ASYNC_GENERATOR


def _code_flags(func: Any) -> int:
    func = getattr(func, "__func__", func)
    while isinstance(func, functools.partial):
        func = func.func
    code = getattr(func, "__code__", None)
    return code.co_flags if code is not None else 0


def code_kind(func: Any) -> int:
    """Вид функции одним числом: ``0`` (обычная) или один из флагов
    ``CO_GENERATOR`` / ``CO_COROUTINE`` / ``CO_ASYNC_GENERATOR``.
    Для объектов без кода (вызываемые классы и т.п.) — ``0``."""
    return _code_flags(func) & _KIND_MASK


async def await_or_return(obj: Any) -> Any:
    if hasattr(obj, "__await__"):
        return await obj
    return obj
