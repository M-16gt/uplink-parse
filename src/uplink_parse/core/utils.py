import asyncio
import inspect
from typing import Any, Callable, Coroutine

from uplink_parse.core._enums import FieldActions

def _name(obj) -> str:
    if isinstance(obj, str):
        return obj
    return getattr(obj, "__qualname__", None) or getattr(obj, "__name__", type(obj).__name__)


async def _to_awaitable(obj):
    if hasattr(obj, "__await__"):
        return await obj
    return obj

def _to_coroutines(items: list) -> list[Coroutine | Callable]:
    return [item() if inspect.iscoroutinefunction(item) else item for item in items]

def to_list(obj) -> list | tuple:
    if isinstance(obj, (list, tuple)):
        return obj
    return [obj] if obj is not None else []

def _resolve(value, fallback):
    """None-safe fallback (unlike `value or fallback`, doesn't misfire on [] / 0 / False)."""
    return fallback if value is None else value

def _apply_post_mutation(hooks: list, mutations: list[Callable]) -> list:
    for mut in mutations:
        mut(hooks)
    return hooks


def _has_async(*callables: Callable) -> bool:
    for c in callables:
        if callable(c) and inspect.iscoroutinefunction(c):
            return True
    return False
