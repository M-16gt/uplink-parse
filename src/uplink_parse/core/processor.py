import asyncio
from typing import Any

from src.uplink_parse.core._generics import ProcessorGeneric, input_rt_func
from src.uplink_parse.core.utils.markers import Markers


class BaseProcessor(ProcessorGeneric[input_rt_func, dict[str, Any]]):
    def __call__(self, func: Any) -> Any:
        setattr(func, Markers.PROCESSOR_CLASS, self.__class__)
        return func

    @classmethod
    async def process(cls, owner: Any, target: dict[str, Any]) -> dict[str, Any]:
        from uplink_parse.core.exceptions import ProcessorCacheError

        try:
            target_meta = owner.storage.parse_funcs_meta[cls]
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

    @staticmethod
    def _populate_target(
        result: dict[str, Any], target: dict[str, Any]
    ) -> dict[str, Any]:
        raise NotImplementedError


async def extract(owner: Any, target: dict[str, Any] | None = None) -> dict[str, Any]:
    target = {} if target is None else target
    try:
        await asyncio.gather(
            *[
                proc_cls.process(owner, target)
                for proc_cls in owner.storage.parse_funcs_meta
            ]
        )
        return target
    except Exception as exc:
        from uplink_parse.core.exceptions import ProcessorError

        if isinstance(exc, ProcessorError):
            raise
        raise ProcessorError(
            f"Extraction failed: {exc}",
            source="_run_extraction",
        ) from exc
