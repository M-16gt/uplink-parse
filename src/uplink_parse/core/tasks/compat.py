from __future__ import annotations

import asyncio
import functools
import inspect
from typing import Any

try:
    import nest_asyncio

    _NEST_ASYNCIO = True
except ImportError:
    _NEST_ASYNCIO = False


_CO_GENERATOR = inspect.CO_GENERATOR
_CO_COROUTINE = inspect.CO_COROUTINE
_CO_ASYNC_GENERATOR = inspect.CO_ASYNC_GENERATOR


def _code_flags(func: Any) -> int:
    func = getattr(func, "func", func)
    while isinstance(func, functools.partial):
        func = func.func
    code = getattr(func, "code", None)
    return code.co_flags if code is not None else 0


def iscoroutinefunction(func: Any) -> bool:
    return bool(_code_flags(func) & _CO_COROUTINE)


def isasyncgenfunction(func: Any) -> bool:
    return bool(_code_flags(func) & _CO_ASYNC_GENERATOR)


def isgeneratorfunction(func: Any) -> bool:
    return bool(_code_flags(func) & _CO_GENERATOR)


def async_to_sync(async_func: Any) -> Any:
    @functools.wraps(async_func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(async_func(*args, **kwargs))

        if _NEST_ASYNCIO:
            nest_asyncio.apply()
            return loop.run_until_complete(async_func(*args, **kwargs))

        raise RuntimeError(
            "Cannot call async function from a running event loop. "
            "Install 'nest-asyncio' or use async API directly."
        ) from None

    return wrapper


def sync_to_async(func: Any) -> Any:
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper


async def await_or_return(obj: Any) -> Any:
    if hasattr(obj, "__await__"):
        return await obj
    return obj
