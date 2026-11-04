"""Накладные расходы библиотеки (без сети и без пользовательской логики).

    python bench/bench_overhead.py                      # проект рядом
    python bench/bench_overhead.py --src /путь/к/src    # другая версия (до/после)
    python bench/bench_overhead.py --n 500 --repeat 5   # быстрее / точнее

Берётся минимум из повторов (как в timeit): он меньше всего зашумлён системой.
Сравнивать числа имеет смысл только между запусками на одной машине.
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import sys
import time
import types
from pathlib import Path


from uplink_parse.core.parse import JSONParse, TextParse  # noqa: E402
from uplink_parse.core.strategies.text import TextStrategy  # noqa: E402
from uplink_parse.core.tasks.task_strategy import BaseTaskStrategy  # noqa: E402
from uplink_parse.core.utils import is_stateless  # noqa: E402
from uplink_parse.core.utils.singleton import get_instance  # noqa: E402
from uplink_parse.decorators import field, fields  # noqa: E402

try:  # новая раскладка / старая
    from uplink_parse.core.parse import ParseConfig
except ImportError:
    from uplink_parse.core._dataclasses import ParseConfig  # type: ignore
try:
    from uplink_parse.decorators import posthook, prehook
except ImportError:
    from uplink_parse.core.hooks import posthook, prehook  # type: ignore

N, REPEAT = 500, 5


# ---------------------------------------------------------------- измерение
def bench(name: str, fn, n: int = N) -> None:
    runs = []
    for _ in range(REPEAT):
        t = time.perf_counter()
        for _ in range(n):
            fn()
        runs.append((time.perf_counter() - t) / n)
    show(name, runs)


def bench_async(name: str, fn, n: int = N) -> None:
    """``fn`` — async-функция без аргументов; цикл событий один на замер,
    поэтому стоимость ``asyncio.run`` в результат не входит."""

    async def loop() -> float:
        t = time.perf_counter()
        for _ in range(n):
            await fn()
        return (time.perf_counter() - t) / n

    show(name, [asyncio.run(loop()) for _ in range(REPEAT)])


def show(name: str, runs: list[float]) -> None:
    print(
        f"  {name:<46}{min(runs) * 1e6:10.2f} µs   (медиана {statistics.median(runs) * 1e6:.2f})"
    )


def section(title: str) -> None:
    print(f"\n{title}")


# ------------------------------------------------------- тестовые данные
RESP = types.SimpleNamespace(
    status_code=200,
    url="https://example.com/page",
    method="GET",
    text="<html>hello</html>",
    json=lambda **kw: {"items": list(range(20)), "name": "x"},
)


def make_fields(count: int, kind: str = "sync") -> dict:
    """``count`` полей одного вида; функции создаются один раз и переиспользуются."""
    ns = {}
    for i in range(count):
        if kind == "sync":

            def f(self, _i=i):
                return _i
        elif kind == "async":

            async def f(self, _i=i):
                return _i
        elif kind == "gen":

            def f(self):
                yield from range(1000)
        elif kind == "agen":

            async def f(self):
                for x in range(1000):
                    yield x

        ns[f"f{i}"] = field(f)
    return ns


def parser(base, ns: dict, **kw):
    return type("P", (base,), dict(ns))(is_decorator=False, **kw)


# -------------------------------------------------------------- сценарии
section("1. Мелкие кирпичи")
bench("is_stateless(класс без init)", lambda: is_stateless(object))
bench("get_instance(стратегия) — из кэша", lambda: get_instance(TextStrategy))


async def _a(self):
    return 1


def _g(self):
    yield 1


async def _ag(self):
    yield 1


for label, f in (
    ("sync", lambda self: 1),
    ("async", _a),
    ("gen", _g),
    ("asyncgen", _ag),
):
    bench(
        f"get_strategy({label}-функция)", lambda f=f: BaseTaskStrategy.get_strategy(f)
    )

section("2. Создание класса и экземпляра (один раз на парсер)")
for count in (10, 100):
    ns = make_fields(count)
    bench(
        f"создание КЛАССА, {count} полей",
        lambda ns=ns: type("P", (TextParse,), dict(ns)),
        n=max(N // 20, 20),
    )
    cls = type("P", (TextParse,), dict(ns))
    bench(
        f"создание ЭКЗЕМПЛЯРА, {count} полей",
        lambda cls=cls: cls(is_decorator=False),
        n=max(N // 20, 20),
    )

section("3. Вызов: накладные расходы на пустые поля")


async def noop():
    return None


bench_async("нижняя граница: await пустой корутины", noop)
base_cfg = ParseConfig(use_thread_for_sync=False)
for count in (1, 10, 100):
    p = parser(TextParse, make_fields(count, "sync"), config=base_cfg)
    bench_async(
        f"{count:>3} sync-полей (без потока)",
        lambda p=p: p(RESP),
        n=max(N // count, 50),
    )
for count in (1, 10, 100):
    p = parser(TextParse, make_fields(count, "async"), config=base_cfg)
    bench_async(f"{count:>3} async-полей", lambda p=p: p(RESP), n=max(N // count, 50))
for count in (1, 10):
    p = parser(TextParse, make_fields(count, "sync"))
    bench_async(
        f"{count:>3} sync-полей (use_thread_for_sync=True)",
        lambda p=p: p(RESP),
        n=max(N // count, 50),
    )

section("4. Генераторы (батчи по 1000 элементов)")
for kind in ("gen", "agen"):
    p = parser(TextParse, make_fields(1, kind))
    bench_async(f"поле-{kind}, 1000 элементов", lambda p=p: p(RESP), n=max(N // 20, 50))

section("5. Хуки")
ns = make_fields(1, "sync")
bare = parser(TextParse, ns, config=base_cfg)
hooked_ns = {"f0": prehook(lambda m: True)(posthook(lambda v, m: v)(ns["f0"]))}
hooked = parser(TextParse, hooked_ns, config=base_cfg)
bench_async("1 поле без хуков", lambda: bare(RESP))
bench_async("1 поле с pre+post хуком", lambda: hooked(RESP))

section("6. Стратегии ответа (1 пустое поле)")
p = parser(TextParse, make_fields(1, "sync"), config=base_cfg)
bench_async("TextParse", lambda: p(RESP))
p = parser(JSONParse, make_fields(1, "sync"), config=base_cfg)
bench_async("JSONParse", lambda: p(RESP))
RAW = types.SimpleNamespace(text="x")  # нет status_code → ответ не преобразуется
p = parser(TextParse, make_fields(1, "sync"), config=base_cfg)
bench_async("без status_code (parse_response пропускается)", lambda: p(RAW))

section("7. Доступ к ctx из поля (1000 обращений к self.response)")


class Access(TextParse):
    @field
    def read(self):
        for _ in range(1000):
            self.response


p = Access(is_decorator=False, config=base_cfg)
bench_async("1000 × self.response", lambda: p(RESP), n=max(N // 20, 50))

section("8. Синхронный вход (asyncio.run внутри call)")
p = parser(TextParse, make_fields(1, "sync"), config=base_cfg)
bench("parser(response) вне цикла событий", lambda: p(RESP), n=max(N // 10, 50))
bench(
    "для сравнения: asyncio.run(пустая корутина)",
    lambda: asyncio.run(noop()),
    n=max(N // 10, 50),
)
