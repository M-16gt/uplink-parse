import asyncio
import inspect
from typing import Any, Callable

from uplink_parse.core._enums import FieldActions

def _name(obj, *attrs: str, **kwargs) -> str:
    name = obj if isinstance(obj, str) else obj.__name__
    for attr in attrs:
        name = getattr(name, attr)()
    for method_name, args in kwargs.items():
        method = getattr(name, method_name)
        if isinstance(args, (list, tuple)):
            name = method(*args)
        elif isinstance(args, dict):
            name = method(**args)
        else:
            name = method(args)

    return name


async def _is_awaitable(obj):
    if hasattr(obj, "__await__"):
        return await obj
    return obj

def _to_coroutines(items):
    return [item() if inspect.iscoroutinefunction(item) else item for item in items]

def _unwrap_singletons(target: dict) -> dict:
    for k, v in target.items():
        if len(v) == 1:
            target[k] = v[0]
    return target

async def _run_tasks(
        func_names: list[str],
        targets: list[Any],
        strategies: list[Any],
        batch_size: int = 200,
        use_thread_for_sync: bool = True,
) -> dict[str, Any]:
    results = [[] for _ in func_names]
    tasks = []

    for i, (tgt, handler) in enumerate(zip(targets, strategies)):
        lst = results[i]

        async def worker(tgt=tgt, handler=handler, lst=lst): # noqa
            try:
                await handler(tgt, lst, batch_size, use_thread_for_sync)
            except Exception as e:
                lst.append(FieldActions.ERROR)

        tasks.append(asyncio.create_task(worker()))

    await asyncio.gather(*tasks)
    return _unwrap_singletons(dict(zip(func_names, results)))


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
