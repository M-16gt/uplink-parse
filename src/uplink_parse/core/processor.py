import asyncio
from typing import Any

from src.uplink_parse.core._dataclasses import _ParseMeta
from src.uplink_parse.core._generics import input_rt_func
from src.uplink_parse.core.exceptions import ProcessorCacheError, ProcessorError
from src.uplink_parse.core.registry import BaseRegistry
from src.uplink_parse.core.singleton import Singleton


class BaseProcessor(BaseRegistry[input_rt_func, dict[str, Any]], Singleton):
    @classmethod
    async def extract(
        cls, owner: Any, target: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        target = {} if target is None else target
        return await cls.process(owner, target)

    @classmethod
    async def process(cls, owner: Any, target: dict[str, Any]) -> dict[str, Any]:
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
    def _populate_target(
        result: dict[str, Any], target: dict[str, Any]
    ) -> dict[str, Any]:
        raise NotImplementedError


def _create_cache_parse_funcs(owner: Any, **kwargs: Any) -> dict[str, _ParseMeta]:
    try:
        return {
            base.__name__: _ParseMeta.from_extractors(base, owner, **kwargs)
            for base in BaseProcessor.__subclasses__()
        }

    except Exception as exc:
        raise ProcessorError(
            f"Failed to create parse function cache: {exc}",
            source="_create_cache_parse_funcs",
        ) from exc


async def extract(owner: Any, target: dict[str, Any] | None = None) -> dict[str, Any]:
    target = {} if target is None else target
    try:
        await asyncio.gather(
            *[base.extract(owner, target) for base in BaseProcessor.__subclasses__()]
        )
        return target
    except Exception as exc:
        if isinstance(exc, ProcessorError):
            raise
        raise ProcessorError(
            f"Extraction failed: {exc}",
            source="_run_extraction",
        ) from exc
