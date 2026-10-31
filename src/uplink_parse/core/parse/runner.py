from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import TYPE_CHECKING, Any

from uplink_parse.core.response_info import ResponseInfo
from uplink_parse.core.utils import to_dict
from uplink_parse.core.utils.ctx import ScraperCtx, ctx

if TYPE_CHECKING:
    from uplink_parse.core.parse.base import BaseParse


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


async def execute_parse(instance: BaseParse[Any, Any], *args: Any) -> Any:
    with ScraperCtx(
        response=args[-1],
        consumer=args[0] if len(args) > 1 else None,
        scraper=instance,
        response_raw=args[-1],
    ):
        ctx.response_info = ResponseInfo()
        if instance.use_parse_response():
            ctx.response = await instance.parse_response()
        return await extract_all(instance)


def run_parse(coro: Coroutine[Any, Any, Any]) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    return coro
