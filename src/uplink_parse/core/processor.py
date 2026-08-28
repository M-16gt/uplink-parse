import asyncio
from typing import Any

from uplink_parse.core._generics import ProcessorGeneric, input_rt_func
from uplink_parse.core.utils import to_dict
from uplink_parse.core.utils.markers import Markers


class BaseProcessor(ProcessorGeneric[input_rt_func, dict[str, Any]]):
    def __call__(self, func: Any) -> Any:
        setattr(func, Markers.PROCESSOR_CLASS, self.__class__)
        return func

    @classmethod
    async def process(cls, owner: Any, target: dict[str, Any]) -> dict[str, Any]:

        target_meta = owner.storage.parse_funcs_meta[cls]

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


async def extract_all(
    owner: Any, target: dict[str, Any] | None = None
) -> dict[str, Any]:
    target = to_dict(target)

    await asyncio.gather(
        *[
            proc_cls.process(owner, target)
            for proc_cls in owner.storage.parse_funcs_meta
        ]
    )
    return target
