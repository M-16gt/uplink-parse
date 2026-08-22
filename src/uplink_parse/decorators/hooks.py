from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from typing import Any

from uplink_parse.core.compat import async_to_sync, await_or_return
from uplink_parse.core.utils import (  # noqa
    _apply_post_mutation,
    _has_async,
    _resolve,
    to_list,
)

_FEATURE_MARKER = object()


class hook:
    __slots__ = ("_hooks", "_post_mutation", "_wrap_condition")

    def __init__(
        self,
        *hooks: Callable,
        post_mutation: list[Callable] | Callable | None = None,
        wrap_condition: Callable[[Any, Callable], bool] | None = None,
    ):
        self._hooks = list(hooks)
        self._post_mutation = to_list(post_mutation)
        self._wrap_condition = wrap_condition
        _apply_post_mutation(self._hooks, self._post_mutation)

    # --- override points -------------------------------------------------

    def _create_async_wrapper(self, active_hooks: list, func: Callable) -> Callable:
        raise NotImplementedError

    def _create_sync_wrapper(
        self, active_hooks: list, func: Callable
    ) -> Callable | None:
        """Optional fast path for all-sync chains (no event loop involved at all).
        Return None to fall back to the async wrapper + sync bridge.
        """
        return None

    def _should_wrap(self, func: Callable, active_hooks: list, wrap_condition) -> bool:
        if not active_hooks:
            return False
        if wrap_condition is not None and not wrap_condition(self, func):
            return False
        return True

    # --- decorator entrypoint --------------------------------------------

    def __call__(
        self,
        func: Callable | None = None,
        *,
        hooks: list[Callable] | Callable | None = None,
        post_mutation: list[Callable] | Callable | None = None,
        wrap_condition: Callable[[Any, Callable], bool] | None = None,
    ) -> Callable:
        if func is None:
            return functools.partial(
                self.__call__,
                hooks=_resolve(hooks, self._hooks),
                post_mutation=_resolve(post_mutation, self._post_mutation),
                wrap_condition=_resolve(wrap_condition, self._wrap_condition),
            )

        active_hooks = to_list(_resolve(hooks, self._hooks))
        _apply_post_mutation(active_hooks, to_list(post_mutation))

        active_wrap_cond = _resolve(wrap_condition, self._wrap_condition)
        if not self._should_wrap(func, active_hooks, active_wrap_cond):
            return func

        is_async_func = inspect.iscoroutinefunction(func)

        if not is_async_func:
            sync_wrapper = self._create_sync_wrapper(active_hooks, func)
            if sync_wrapper is not None:
                return functools.wraps(func)(sync_wrapper)

        async_wrapper = functools.wraps(func)(
            self._create_async_wrapper(active_hooks, func)
        )
        return async_wrapper if is_async_func else async_to_sync(async_wrapper)


class prehooks(hook):  # noqa
    async def _start(
        self, active_hooks: list, args: list, kwargs: dict, func: Callable
    ) -> Any:
        for h in active_hooks:
            hook_res = await await_or_return(h(args, kwargs, func))
            if hook_res is not True:
                return hook_res
        return True

    def _create_async_wrapper(self, active_hooks, func):
        async def wrapper(*args, **kwargs):
            args_list = list(args)
            res = await self._start(active_hooks, args_list, kwargs, func)
            if res is not True:
                return res
            return await await_or_return(func(*args_list, **kwargs))

        return wrapper

    def _create_sync_wrapper(self, active_hooks, func):
        if _has_async(func, *active_hooks):
            return None

        def wrapper(*args, **kwargs):
            args_list = list(args)
            for h in active_hooks:
                res = h(args_list, kwargs, func)
                if res is not True:
                    return res
            return func(*args_list, **kwargs)

        return wrapper


class posthooks(hook):  # noqa
    async def _start(self, active_hooks, result):
        current_res = result
        for h in active_hooks:
            current_res = await await_or_return(h(current_res))
        return current_res

    def _create_async_wrapper(self, active_hooks, func):
        async def wrapper(*args, **kwargs):
            original_res = await await_or_return(func(*args, **kwargs))
            return await self._start(active_hooks, original_res)

        return wrapper

    def _create_sync_wrapper(self, active_hooks, func):
        if _has_async(func, *active_hooks):
            return None

        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            for h in active_hooks:
                result = h(result)
            return result

        return wrapper


class composehook(hook):  # noqa
    def __init__(
        self,
        *hooks: Callable,
        post_mutation: list[Callable] | Callable | None = None,
        wrap_condition: Callable[[Any, Callable], bool] | None = None,
    ):
        super().__init__(*hooks, post_mutation=None, wrap_condition=wrap_condition)
        self._hooks = self._hooks + [_FEATURE_MARKER]
        self._post_mutation = to_list(post_mutation)
        _apply_post_mutation(self._hooks, self._post_mutation)

    @staticmethod
    def _resolve_hooks(active_hooks: list, func: Callable) -> list:
        return [func if h is _FEATURE_MARKER else h for h in active_hooks]

    async def _start(self, active_hooks, *args, **kwargs):
        res = await await_or_return(active_hooks[0](*args, **kwargs))
        for f in active_hooks[1:]:
            res = await await_or_return(f(res))
        return res

    def _create_async_wrapper(self, active_hooks, func):
        resolved = self._resolve_hooks(active_hooks, func)

        async def wrapper(*args, **kwargs):
            return await self._start(resolved, *args, **kwargs)

        return wrapper

    def _create_sync_wrapper(self, active_hooks, func):
        resolved = self._resolve_hooks(active_hooks, func)
        if _has_async(*resolved):
            return None

        def wrapper(*args, **kwargs):
            res = resolved[0](*args, **kwargs)
            for f in resolved[1:]:
                res = f(res)
            return res

        return wrapper


class errorhook(hook):
    async def _start(self, active_hooks, func, exception):
        for h in active_hooks:
            try:
                return await await_or_return(h(exception, func))
            except Exception:  # noqa
                continue
        raise exception

    def _create_async_wrapper(self, active_hooks, func):
        async def wrapper(*args, **kwargs):
            try:
                return await await_or_return(func(*args, **kwargs))
            except Exception as e:
                return await self._start(active_hooks, func, e)

        return wrapper

    def _create_sync_wrapper(self, active_hooks, func):
        if _has_async(func, *active_hooks):
            return None

        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                for h in active_hooks:
                    try:
                        return h(e, func)
                    except Exception:  # noqa
                        continue
                raise e

        return wrapper
