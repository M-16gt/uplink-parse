from __future__ import annotations

import asyncio
import functools
import inspect
from typing import Any, Callable, Coroutine

try:
    import nest_asyncio

    _NEST_ASYNCIO = True
except ImportError:
    _NEST_ASYNCIO = False


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


def to_runnable(*funcs: Any) -> list[Coroutine[Any, Any, Any] | Callable[..., Any]]:
    return [func() if inspect.iscoroutinefunction(func) else func for func in funcs]
