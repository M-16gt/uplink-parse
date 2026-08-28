from __future__ import annotations

import asyncio
import functools
from typing import Any

from typing_extensions import Self

from uplink_parse.core.parseable import Parseable
from uplink_parse.core.utils import to_dict
from uplink_parse.core.utils.singleton import get_instance

try:
    from uplink import response_handler
except ImportError:

    def response_handler(handler: Any, requires_consumer: bool = False) -> Any:
        return handler


from uplink_parse.core._dataclasses import Storage, _ParseMeta
from uplink_parse.core._generics import ParseGeneric, strategy, strategy_rt
from uplink_parse.core.processor import extract_all
from uplink_parse.core.strategies import (
    BytesResult,
    BytesStrategy,
    JSONResult,
    JSONStrategy,
    TextResult,
    TextStrategy,
    XMLResult,
    XMLStrategy,
)
from uplink_parse.core.tasks.task_runner import TaskRunner
from uplink_parse.core.utils.ctx import ScraperCtx, ctx


class _ParseObj(ParseGeneric[strategy, strategy_rt]):
    scraper: Self
    response: strategy_rt
    consumer: Any
    request: Any

    def __getattr__(self, item: str) -> Any:
        return getattr(ctx, item)


class BaseParse(Parseable, _ParseObj[strategy, strategy_rt]):
    storage: Storage

    def __new__(
        cls,
        *,
        is_decorator: bool = True,
        strategy_params: dict[str, Any] | None = None,
    ) -> Any:
        instance = super().__new__(cls)
        parse_funcs_meta = _ParseMeta.build_all(instance)
        task_runner = TaskRunner()
        instance.storage = Storage(
            parse_funcs_meta=parse_funcs_meta,
            task_runner=task_runner,
        )
        instance.parse_response = functools.partial(  # type: ignore[method-assign]
            instance.parse_response, **to_dict(strategy_params)
        )
        return instance if not is_decorator else parse(instance)

    async def _call_async(self, *args: Any, **kwargs: Any) -> Any:
        with ScraperCtx(
            response=args[-1],
            consumer=args[0] if len(args) > 1 else None,
            scraper=self,
            request=args[-1],
        ):
            if self.use_parse_response():
                ctx.response = await self.parse_response()
            return await extract_all(self)

    @functools.wraps(_call_async)
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        coro = self._call_async(*args, **kwargs)
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        return coro

    async def parse_response(self, **strategy_params: Any) -> Any:
        return await get_instance(self.config_types["strategy"])(
            ctx.request, **strategy_params
        )

    @staticmethod
    def use_parse_response() -> bool:
        return bool(getattr(ctx.request, "status_code", None))


class TextParse(BaseParse[TextStrategy, TextResult]): ...


class XMLParse(BaseParse[XMLStrategy, XMLResult]): ...


class JSONParse(BaseParse[JSONStrategy, JSONResult]): ...


class BytesParse(BaseParse[BytesStrategy, BytesResult]): ...


def parse(cls: BaseParse[Any, Any]) -> Any:
    return response_handler(cls.__call__, requires_consumer=True)
