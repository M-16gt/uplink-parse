import asyncio
from typing import Any

from src.uplink_parse.core._dataclasses import _ParseMeta
from src.uplink_parse.core._generics import input_rt_func
from src.uplink_parse.core.exceptions import ProcessorCacheError, ProcessorError
from src.uplink_parse.core.registry import BaseRegistry
from src.uplink_parse.core.utils.cached import Cached


class BaseProcessor(BaseRegistry[input_rt_func, dict[str, Any]], Cached):
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
            return cls._populate_target(
                await owner.storage.task_runner(target_meta.funcs), target
            )
        return target

    @classmethod
    def build_parse_meta(cls, owner: Any, **kwargs: Any) -> dict[str, _ParseMeta]:
        return {
            base.__name__: _ParseMeta.from_extractors(base, owner, **kwargs)
            for base in cls.__subclasses__()
        }

    @staticmethod
    def _populate_target(
        result: dict[str, Any], target: dict[str, Any]
    ) -> dict[str, Any]:
        raise NotImplementedError


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
