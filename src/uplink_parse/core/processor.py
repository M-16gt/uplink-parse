import asyncio
from collections import defaultdict
from typing import Any

from uplink_parse.core.registry import BaseRegistry
from uplink_parse.core._generics import input_rt_func
from uplink_parse.core._dataclasses import _ParseMeta, FuncMeta
from uplink_parse.core.singleton import Singleton
from uplink_parse.core.task_strategy import BaseTaskStrategy
from uplink_parse.core.utils import _to_coroutines
from uplink_parse.core.exceptions import ProcessorError, ProcessorCacheError


class BaseProcessor(BaseRegistry[input_rt_func, dict], Singleton):
    """
    Базовый процессор. Отвечает только за извлечение СВОИХ данных.
    """

    @classmethod
    async def extract(cls, owner: Any, target: dict | None = None) -> dict[str, Any]:
        target = {} if target is None else target
        return await cls.process(owner, target)

    @classmethod
    async def process(cls, owner: Any, target: dict) -> dict[str, Any]:
        try:
            target_meta = owner.storage.parse_funcs_meta[cls.__name__]
        except (AttributeError, KeyError) as exc:
            raise ProcessorCacheError(
                f"Parse cache missing for processor {cls.__name__}. "
                "Ensure the owner instance was initialized correctly.",
                source=f"{cls.__name__}.process",
                details={"owner": type(owner).__name__, "processor": cls.__name__},
            ) from exc

        if not target_meta.is_nan_obj():
            runner = owner.storage.task_runner
            return cls._populate_target(await runner(target_meta.funcs), target)
        return target

    @staticmethod
    def _populate_target(result: dict[str, Any], target: dict) -> dict:
        raise NotImplementedError


def _create_cache_parse_funcs(owner, **kwargs) -> defaultdict[str, _ParseMeta]:
    try:
        result = defaultdict(_ParseMeta)
        owner_class = owner.__class__
        for base in BaseProcessor.__subclasses__():
            names = list(base.get_registered(owner_class, **kwargs))
            urls = [getattr(owner, name) for name in names]
            coroutines_or_funcs = _to_coroutines(urls)
            strategies = [BaseTaskStrategy.get_strategy(tgt) for tgt in coroutines_or_funcs]

            funcs = [
                FuncMeta(name=name, url=url, coroutine_or_func=cof, strategy=strat)
                for name, url, cof, strat in zip(names, urls, coroutines_or_funcs, strategies)
                if name and url is not None and cof is not None and strat is not None
            ]

            result[base.__name__] = _ParseMeta(funcs=funcs)
        return result

    except Exception as exc:
        raise ProcessorError(
            f"Failed to create parse function cache: {exc}",
            source="_create_cache_parse_funcs",
        ) from exc


async def extract(owner: Any, target: dict | None = None) -> dict:
    target = {} if target is None else target
    try:
        await asyncio.gather(*[
            base.extract(owner, target) for base in BaseProcessor.__subclasses__()
        ])
    except Exception as exc:
        if isinstance(exc, ProcessorError):
            raise
        raise ProcessorError(
            f"Extraction failed: {exc}",
            source="_run_extraction",
        ) from exc
    return target