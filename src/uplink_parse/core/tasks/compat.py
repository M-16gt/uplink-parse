from __future__ import annotations

import functools
import inspect
from typing import Any

_CO_GENERATOR = inspect.CO_GENERATOR
_CO_COROUTINE = inspect.CO_COROUTINE
_CO_ASYNC_GENERATOR = inspect.CO_ASYNC_GENERATOR


def _code_flags(func: Any) -> int:
    func = getattr(func, "__func__", func)
    while isinstance(func, functools.partial):
        func = func.func
    code = getattr(func, "__code__", None)
    return code.co_flags if code is not None else 0


def iscoroutinefunction(func: Any) -> bool:
    return bool(_code_flags(func) & _CO_COROUTINE)


def isasyncgenfunction(func: Any) -> bool:
    return bool(_code_flags(func) & _CO_ASYNC_GENERATOR)


def isgeneratorfunction(func: Any) -> bool:
    return bool(_code_flags(func) & _CO_GENERATOR)


async def await_or_return(obj: Any) -> Any:
    if hasattr(obj, "__await__"):
        return await obj
    return obj
