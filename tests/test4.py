import asyncio
import atexit
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from functools import wraps
from typing import Any, Callable, TypeVar

T = TypeVar("T")

_BRIDGE_POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="uplink_parse.bridge")
atexit.register(_BRIDGE_POOL.shutdown, wait=True)

def _async_to_sync(async_func: Callable[..., T]) -> Callable[..., T]:
    @wraps(async_func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        ctx = copy_context()
        try:
            asyncio.get_running_loop()
            return _BRIDGE_POOL.submit(lambda : asyncio.run(async_func(*args, **kwargs))).result()
        except RuntimeError:
            return asyncio.run(async_func(*args, **kwargs))
    return wrapper