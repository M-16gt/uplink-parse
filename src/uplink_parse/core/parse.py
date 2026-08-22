from __future__ import annotations

from typing import Any

from typing_extensions import Self

from uplink_parse.core.tasks.compat import async_to_sync

try:
    from uplink import response_handler
except ImportError:

    def response_handler(handler: Any, requires_consumer: bool = False) -> Any:
        return handler


from src.uplink_parse.core._dataclasses import Storage
from src.uplink_parse.core._generics import ParseGeneric, strategy, strategy_rt
from src.uplink_parse.core.processor import BaseProcessor, extract
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
from src.uplink_parse.core.utils.cached import Cached
from uplink_parse.core.tasks.task_runner import TaskRunner
from uplink_parse.core.utils.ctx import ScraperCtx, ctx


class _ParseObj(ParseGeneric[strategy, strategy_rt], Cached):
    scraper: Self
    response: strategy_rt
    consumer: Any
    request: Any

    def __getattr__(self, item: str) -> Any:
        return getattr(ctx, item)


class BaseParse(_ParseObj[strategy, strategy_rt]):
    storage: Storage

    def __new__(
        cls,
        *,
        is_decorator: bool = True,
        is_async: bool = False,
        registry_params: dict[str, Any] | None = None,
        strategy_params: dict[str, Any] | None = None,
    ) -> Any:
        instance = super().__new__(cls)

        parse_funcs_meta = BaseProcessor.build_parse_meta(
            instance,
            **(registry_params if registry_params is not None else {"check_mro": True}),
        )
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
            if self.use_parse_response():
                ctx.response = await self.parse_response()
            start = time.time()
            result = await extract(self, {})
            print(time.time() - start)
            return result

    @classmethod
    async def parse_response(cls) -> Any:
        return await cls.config_types["strategy"]()(
            ctx.request, cls.storage.strategy_params
        )

    @staticmethod
    def use_parse_response() -> bool:
        return bool(getattr(ctx.request, "status_code", None))


class TextParse(BaseParse[TextStrategy, TextResult]): ...


class XMLParse(BaseParse[XMLStrategy, XMLResult]): ...


class JSONParse(BaseParse[JSONStrategy, JSONResult]): ...


class BytesParse(BaseParse[BytesStrategy, BytesResult]): ...


def parse(cls: BaseParse[Any, Any]) -> Any:
    """Декоратор для интеграции с uplink."""
    h = response_handler(cls.__call__, requires_consumer=True)
    return h
