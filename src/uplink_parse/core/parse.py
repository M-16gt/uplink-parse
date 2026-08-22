from __future__ import annotations

from typing import Any

from typing_extensions import Self

from src.uplink_parse.core.compat import async_to_sync

try:
    from uplink import response_handler
except ImportError:

    def response_handler(handler: Any, requires_consumer: bool = False) -> Any:
        return handler


from src.uplink_parse.core._dataclasses import Storage
from src.uplink_parse.core._generics import ParseGeneric, strategy, strategy_rt
from src.uplink_parse.core._strategies import (
    BS4Result,
    BS4Strategy,
    BytesResult,
    BytesStrategy,
    JSONResult,
    JSONStrategy,
    TextResult,
    TextStrategy,
    XMLResult,
    XMLStrategy,
)
from src.uplink_parse.core.cached import Cached
from src.uplink_parse.core.ctx import ScraperCtx, ctx
from src.uplink_parse.core.processor import BaseProcessor, extract
from src.uplink_parse.core.task_runner import TaskRunner


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
        _registry_params: dict[str, Any] | None = None,
    ) -> Any:
        instance = super().__new__(cls)

        parse_funcs_meta = BaseProcessor.build_parse_meta(
            instance, **(_registry_params or {"check_mro": True})
        )
        task_runner = TaskRunner()
        instance.storage = Storage(
            parse_funcs_meta=parse_funcs_meta, task_runner=task_runner
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
                ctx.response = await self.parse_response()  # type: ignore[attr-defined]
            start = time.time()
            result = await extract(self, {})
            print(time.time() - start)
            return result

    @classmethod
    async def parse_response(cls) -> Any:
        return await cls.config_types["strategy"]()(ctx.request)

    @staticmethod
    def use_parse_response() -> bool:
        return bool(getattr(ctx.request, "status_code", None))


class BS4Parse(BaseParse[BS4Strategy, BS4Result]): ...


class TextParse(BaseParse[TextStrategy, TextResult]): ...


class XMLParse(BaseParse[XMLStrategy, XMLResult]): ...


class JSONParse(BaseParse[JSONStrategy, JSONResult]): ...


class BytesParse(BaseParse[BytesStrategy, BytesResult]): ...


def parse(cls: BaseParse[Any, Any]) -> Any:
    """Декоратор для интеграции с uplink."""
    h = response_handler(cls.__call__, requires_consumer=True)
    return h
