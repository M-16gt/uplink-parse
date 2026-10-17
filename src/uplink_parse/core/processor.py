import asyncio
from collections.abc import Callable
from typing import Any, TypeVar

from uplink_parse.core._dataclasses import FuncMeta, PopulateFunc, meta_decorator
from uplink_parse.core.tasks.task_strategy import BaseTaskStrategy
from uplink_parse.core.utils import to_dict

__all__ = ["PopulateFunc", "processor", "extract_all"]

F = TypeVar("F", bound=Callable[..., Any])


def processor(populate: PopulateFunc) -> Callable[[F], F]:
    """Фабрика декораторов-процессоров.

    Поля с одинаковой ``populate`` выполняются одной группой, а их результат
    вливается в ответ именно этой функцией::

        field = processor(lambda result, target: target | result)
    """

    def update(meta: FuncMeta) -> None:
        meta.populate = populate
        meta.strategy = BaseTaskStrategy.get_strategy(meta.func)

    return meta_decorator(update)


async def extract_all(
    owner: Any, target: dict[str, Any] | None = None
) -> dict[str, Any]:
    target = to_dict(target)
    groups = owner.storage.parse_funcs_meta
    results = await asyncio.gather(
        *[owner.storage.task_runner(metas) for metas in groups.values()]
    )
    for populate, result in zip(groups, results, strict=True):
        target = populate(result, target)
    return target
