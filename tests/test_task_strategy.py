import functools
from typing import Any

from uplink_parse.core.parse.text import TextParse
from uplink_parse.core.tasks import BaseTaskStrategy
from uplink_parse.core.tasks.task_strategy import (
    _FuncAsyncGenStrategy,
    _FuncAsyncStrategy,
    _FuncSyncGenStrategy,
    _FuncSyncStrategy,
    select_strategy,
)
from uplink_parse.decorators import field


def _sync() -> None: ...


def _gen():  # type: ignore[no-untyped-def]
    yield


async def _coro() -> None: ...


async def _agen():  # type: ignore[no-untyped-def]
    yield


class _Owner:
    def method(self) -> None: ...

    async def agen(self):  # type: ignore[no-untyped-def]
        yield


def test_builtin_kinds_are_selected_by_code_flags() -> None:
    cases = {
        _sync: _FuncSyncStrategy,
        lambda: 1: _FuncSyncStrategy,
        _gen: _FuncSyncGenStrategy,
        _coro: _FuncAsyncStrategy,
        _agen: _FuncAsyncGenStrategy,
        functools.partial(_coro): _FuncAsyncStrategy,
        _Owner().method: _FuncSyncStrategy,
        _Owner().agen: _FuncAsyncGenStrategy,
    }
    for target, expected in cases.items():
        assert type(select_strategy(target)) is expected, target


def test_callable_object_without_code_falls_back_to_sync() -> None:
    class Callable:
        def __call__(self) -> None: ...

    assert type(select_strategy(Callable())) is _FuncSyncStrategy


class Spec:
    """Как ``glom.T``: не функция, но вызываемый объект."""

    def __init__(self, value: str) -> None:
        self.value = value

    def __call__(self, *args: Any, **kwargs: Any) -> "Spec":
        return self


class SubSpec(Spec): ...


# Объявлена ПОСЛЕ встроенных: раньше такую стратегию перекрывал catch-all
# ``callable(target)`` и она не выбиралась никогда.
class SpecStrategy(BaseTaskStrategy, targets=(Spec,)):
    async def __call__(
        self, target: Any, lst: list[Any], batch_size: int, use_thread: bool
    ) -> None:
        spec = target.func.__func__  # partial(MethodType(spec, owner))
        self._flush_batch(lst, [f"spec:{spec.value}"])


def test_custom_strategy_wins_over_callable_fallback() -> None:
    assert type(select_strategy(Spec("x"))) is SpecStrategy
    assert type(select_strategy(SubSpec("x"))) is SpecStrategy  # через MRO


def test_custom_strategy_is_a_stateless_singleton() -> None:
    assert select_strategy(Spec("a")) is select_strategy(Spec("b"))


def test_custom_strategy_runs_as_a_field() -> None:
    class Page(TextParse):
        value = field(Spec("hello"))

        @field
        def plain(self) -> str:
            return "ok"

    assert Page(is_decorator=False)("body") == {"value": "spec:hello", "plain": "ok"}
