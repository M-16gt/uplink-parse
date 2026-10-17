from __future__ import annotations

from collections.abc import Callable
from typing import Any

from uplink_parse.core._dataclasses import HookPoint, HookSpec, meta_decorator

__all__ = ["SKIP", "HookPoint", "HookSpec", "prehook", "posthook", "errorhook"]


class _SkipType:
    """Сентинел: поле (PRE) или конкретный элемент (POST) выбрасывается
    из результата. Не исключение — дешевле в async-пайплайне и не путает
    control-flow с реальными ошибками."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "SKIP"

    def __bool__(self) -> bool:
        return False


SKIP = _SkipType()


def _register(point: HookPoint, *funcs: Callable[..., Any]) -> Callable[..., Any]:
    return meta_decorator(lambda meta: meta.hooks.of(point).extend(funcs))


def prehook(*funcs: Callable[..., Any]) -> Callable[..., Any]:
    """h(func_meta) -> SKIP | True | Any.
    SKIP — поле пропускается целиком.
    True — идём вызывать функцию поля как обычно.
    Any (иное) — это и есть финальный результат поля, сама функция не зовётся.
    """
    return _register(HookPoint.PRE, *funcs)


def posthook(*funcs: Callable[..., Any]) -> Callable[..., Any]:
    """h(value) -> SKIP | Any. Прогоняется по каждому элементу результата поля."""
    return _register(HookPoint.POST, *funcs)


def errorhook(*funcs: Callable[..., Any]) -> Callable[..., Any]:
    """h(exc, func_meta) -> Any | raise. Первый хук, не бросивший исключение,
    определяет результат (или SKIP, чтобы проглотить ошибку без значения)."""
    return _register(HookPoint.ERROR, *funcs)
