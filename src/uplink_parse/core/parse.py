from __future__ import annotations

from typing import Any, cast

from typing_extensions import Self

from tests.test4 import _async_to_sync

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
from src.uplink_parse.core.ctx import ScraperCtx, ctx
from src.uplink_parse.core.processor import _create_cache_parse_funcs, extract
from src.uplink_parse.core.singleton import Singleton
from src.uplink_parse.core.task_runner import TaskRunner


class _ParseObj(ParseGeneric[strategy, strategy_rt], Singleton):
    @property
    def scraper(self) -> Self:
        return cast(Self, ctx.scraper)

    @property
    def response(self) -> strategy_rt:
        return cast(strategy_rt, ctx.response)

    @property
    def consumer(self) -> Any:
        return ctx.consumer

    @property
    def request(self) -> Any:
        return ctx.request


class BaseParse(_ParseObj[strategy, strategy_rt]):
    def __new__(
        cls,
        *,
        is_decorator: bool = True,
        is_async: bool = False,
        _registry_params: dict[str, Any] | None = None,
    ) -> Any:
        instance = super().__new__(cls)
        parse_funcs_meta = _create_cache_parse_funcs(
            instance, **(_registry_params or {"check_mro": True})
        )
        task_runner = TaskRunner()
        instance.storage = Storage(  # type: ignore[attr-defined, call-arg]
            parse_funcs_meta=parse_funcs_meta, task_runner=task_runner
        )
        instance.__call__ = (  # type: ignore[method-assign]
            instance.__call__ if is_async else _async_to_sync(instance.__call__)
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
