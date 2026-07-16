import asyncio
from collections import defaultdict
from typing import Any

from uplink_parse.core.registry import BaseRegistry
from uplink_parse.core._generics import input_rt_func, output_rt_func
from uplink_parse.core._dataclasses import _ParseMeta
from uplink_parse.core.singleton import Singleton
from uplink_parse.core.utils import _run_tasks, _to_coroutines
from uplink_parse.core.task_strategy import BaseTaskStrategy
from uplink_parse.core.exceptions import PopulateTargetNotImplementedError


class BaseProcessor(BaseRegistry[input_rt_func, output_rt_func], Singleton):
    """
    Базовый процессор, который находит зарегистрированные методы у объекта-владельца
    и заполняет ими целевой словарь (контекст).
    """

    @classmethod
    async def process(
            cls,
            owner: Any,
            target: dict
    ) -> dict[str, Any]:
        """
        Основной метод запуска.

        :param owner: Экземпляр класса, у которого нужно вызвать зарегистрированные методы.
        :param target: Словарь, куда будут записаны результаты. Если None, создается новый.
        :return: Заполненный словарь target.
        """
        target_meta = owner._cache_parse_funcs[cls.__name__]  # noqa
        if not target_meta.is_nan_obj():
            return cls._populate_target(await _run_tasks(target_meta.names, target_meta.coroutines_or_funcs, target_meta.strategies), target)
        return target

    @staticmethod
    def _populate_target(
            result: dict[str, Any],
            target: dict
    ) -> dict:
        raise PopulateTargetNotImplementedError(
            "Subclasses of BaseProcessor must implement _populate_target()."
        )


def _create_cache_parse_funcs(owner, **kwargs) -> defaultdict[str, _ParseMeta]:
    result = defaultdict(_ParseMeta)
    owner_class = owner.__class__
    for base in BaseProcessor.__subclasses__():
        names = list(base.get_registered(owner_class, **kwargs))
        urls = [getattr(owner, name) for name in names]
        coroutines_or_funcs = _to_coroutines(urls)
        strategies = [BaseTaskStrategy.get_strategy(tgt) for tgt in coroutines_or_funcs]
        result[base.__name__] = _ParseMeta(names, urls, coroutines_or_funcs, strategies)
    return result


from uplink_parse.future import _


@_
async def extract(owner: Any, target: dict | None = None) -> dict:
    target = {} if target is None else target
    await asyncio.gather(*[base.process(owner, target) for base in BaseProcessor.__subclasses__()])
    return target