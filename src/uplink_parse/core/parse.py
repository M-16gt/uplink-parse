from __future__ import annotations

from typing import Any

from typing_extensions import Self

from src.uplink_parse.core.parseable import Parseable
from src.uplink_parse.core.tasks.compat import async_to_sync
from uplink_parse.core.utils.singleton import get_instance

try:
    from uplink import response_handler
except ImportError:

    def response_handler(handler: Any, requires_consumer: bool = False) -> Any:
        return handler


from src.uplink_parse.core._dataclasses import Storage, _ParseMeta
from src.uplink_parse.core._generics import ParseGeneric, strategy, strategy_rt
from src.uplink_parse.core.processor import extract
from src.uplink_parse.core.strategies import (
    BytesResult,
    BytesStrategy,
    JSONResult,
    JSONStrategy,
    TextResult,
    TextStrategy,
    XMLResult,
    XMLStrategy,
)
from src.uplink_parse.core.tasks.task_runner import TaskRunner
from src.uplink_parse.core.utils.ctx import ScraperCtx, ctx


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
        is_async: bool = False,
        strategy_params: dict[str, Any] | None = None,
    ) -> Any:
        instance = super().__new__(cls)

        parse_funcs_meta = _ParseMeta.build_all(instance)
        task_runner = TaskRunner()
        instance.storage = Storage(
            parse_funcs_meta=parse_funcs_meta,
            task_runner=task_runner,
            strategy_params=strategy_params or {},
        )

        instance.__call__ = (  # type: ignore[method-assign]
            instance.__call__ if is_async else async_to_sync(instance.__call__)
        )
        return instance if not is_decorator else parse(instance)

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        import time

        with ScraperCtx(
            response=args[-1],
            consumer=args[0] if len(args) > 1 else None,
            scraper=self,
            request=args[-1],
        ) as _:
            start = time.time()
            if self.use_parse_response():
                ctx.response = await self.parse_response()
                print(time.time() - start)
            start = time.time()
            result = await extract(self, {})
            print(time.time() - start)
            return result

    async def parse_response(self) -> Any:
        return await get_instance(self.config_types["strategy"])(
            ctx.request, **self.storage.strategy_params
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
