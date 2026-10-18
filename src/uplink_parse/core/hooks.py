from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from uplink_parse.core._dataclasses import HookPoint, HookSpec, get_func_meta
from uplink_parse.core.utils.markers import Markers

__all__ = [
    "SKIP",
    "UNHANDLED",
    "HookPoint",
    "HookSpec",
    "prehook",
    "paramshook",
    "posthook",
    "errorhook",
]


class _Signal:
    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return self.name

    def __bool__(self) -> bool:
        return False


SKIP = _Signal("SKIP")
UNHANDLED = _Signal("UNHANDLED")
T = TypeVar("T")


def _register(point: HookPoint, *hooks: Callable[..., Any]) -> Callable[[T], T]:
    def decorate(target: T) -> T:
        if isinstance(target, type):
            spec = vars(target).get(Markers.HOOKS)
            if spec is None:
                spec = HookSpec()
                setattr(target, Markers.HOOKS, spec)
        else:
            spec = get_func_meta(target).hooks
        spec.of(point).extend(hooks)
        return target

    return decorate


def class_hooks_of(owner: Any) -> tuple[HookSpec, ...]:
    """Хуки классов по MRO: от базового класса к наследнику."""
    return tuple(
        spec
        for base in reversed(type(owner).__mro__)
        if isinstance((spec := vars(base).get(Markers.HOOKS)), HookSpec)
    )


def prehook(*hooks: Callable[..., Any]) -> Callable[[T], T]:
    """hook(meta) -> True (вызвать поле) | SKIP | замена результата."""
    return _register(HookPoint.PRE, *hooks)


def paramshook(*hooks: Callable[..., Any]) -> Callable[[T], T]:
    """hook(meta) -> словарь именованных аргументов функции поля."""
    return _register(HookPoint.PARAMS, *hooks)


def posthook(*hooks: Callable[..., Any]) -> Callable[[T], T]:
    """hook(value, meta) -> обработанный результат всего поля | SKIP."""
    return _register(HookPoint.POST, *hooks)


def errorhook(*hooks: Callable[..., Any]) -> Callable[[T], T]:
    """hook(exc, meta) -> запасное значение | SKIP | UNHANDLED."""
    return _register(HookPoint.ERROR, *hooks)
