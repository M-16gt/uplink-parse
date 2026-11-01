from collections.abc import Callable
from typing import Any, TypeVar

from uplink_parse.core.tasks.task_strategy import BaseTaskStrategy
from uplink_parse.decorators.meta import FuncMeta, PopulateFunc, meta_decorator

__all__ = ["PopulateFunc", "processor", "field", "fields"]

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


def _field_populate(result: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    target.update(result)
    return target


def _fields_populate(result: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    for d in result.values():
        target.update(d)
    return target


field = processor(_field_populate)
fields = processor(_fields_populate)
