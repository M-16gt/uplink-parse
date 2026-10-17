from __future__ import annotations

from collections.abc import Callable
from typing import Any

from uplink_parse.core._dataclasses import HookSpec, get_func_meta

__all__ = ["SKIP", "HookSpec", "prehook", "posthook", "errorhook"]


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


def _register(point: str, *funcs: Callable[..., Any]) -> Callable[..., Any]:
    def deco(target: Callable[..., Any]) -> Callable[..., Any]:
        getattr(get_func_meta(target).hooks, point).extend(funcs)
        return target

    return deco


def prehook(*funcs: Callable[..., Any]) -> Callable[..., Any]:
    """h(func_meta) -> SKIP | True | Any.
    SKIP — поле пропускается целиком.
    True — идём вызывать функцию поля как обычно.
    Any (иное) — это и есть финальный результат поля, сама функция не зовётся.
    """
    return _register("pre", *funcs)


def posthook(*funcs: Callable[..., Any]) -> Callable[..., Any]:
    """h(value) -> SKIP | Any. Прогоняется по каждому элементу результата поля."""
    return _register("post", *funcs)


def errorhook(*funcs: Callable[..., Any]) -> Callable[..., Any]:
    """h(exc, func_meta) -> Any | raise. Первый хук, не бросивший исключение,
    определяет результат (или SKIP, чтобы проглотить ошибку без значения)."""
    return _register("error", *funcs)
