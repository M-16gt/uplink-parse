from __future__ import annotations

from typing import Callable, Self

from test4 import _async_to_sync

try:
    from uplink import response_handler
except ImportError:
    response_handler = lambda handler, requires_consumer=False: handler

__all__ = ("BS4Parse", "XMLParse", "TextParse", "JSONParse", "BytesParse", "BaseParse")


from uplink_parse.core.singleton import Singleton
from uplink_parse.core.processor import extract, _create_cache_parse_funcs
from uplink_parse.core._generics import ParseGeneric, strategy, strategy_rt
from uplink_parse.core._strategies import *
from uplink_parse.core.ctx import ctx, ScraperCtx
from uplink_parse.core.utils import _is_awaitable
from uplink_parse.core._dataclasses import Storage

class _ParseObj(ParseGeneric[strategy, strategy_rt], Singleton):

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.storage = Storage()

    @property
    def scraper(self) -> Self:
        return ctx.scraper

    @property
    def response(self) -> strategy_rt:
        return ctx.response

    @property
    def consumer(self):
        return ctx.consumer

    @property
    def request(self):
        return ctx.request

class BaseParse(_ParseObj[strategy, strategy_rt]):
    def __new__(cls, *, is_decorator: bool = True, is_async: bool = False, _registry_params: dict | None = None) -> response_handler | BaseParse:
        instance = super().__new__(cls)
        instance.__call__ = instance.__async_call__ if is_async else _async_to_sync(instance.__async_call__)
        instance._cache_parse_funcs = _create_cache_parse_funcs(instance, **_registry_params or {"check_mro": True})
        return instance if not is_decorator else parse(instance)

    async def __async_call__(self, *args, **kwargs):
        import time
        with ScraperCtx(response=args[-1], consumer=args[0] if len(args) > 1 else None, scraper=self, request=args[-1]) as _:
            if self.use_parse_response(): ctx.response = await self.parse_response()
            start = time.time()
            result = self.get_model()(**await extract(self, {}))
            print(time.time() - start)
            return result


    @classmethod
    async def parse_response(cls) -> strategy_rt:
        return await _is_awaitable(cls.config_types["strategy"]()(ctx.request))

    @staticmethod
    def use_parse_response() -> bool:
        return bool(getattr(ctx.request, "status_code", None))

    @staticmethod
    def get_model() -> Callable:
        return lambda **kwargs: kwargs

class BS4Parse(BaseParse[BS4Strategy, BS4Result]):
    ...

class TextParse(BaseParse[TextStrategy, TextResult]):
    ...

class XMLParse(BaseParse[XMLStrategy, XMLResult]):
    ...

class JSONParse(BaseParse[JSONStrategy, JSONResult]):
    ...

class BytesParse(BaseParse[BytesStrategy, BytesResult]):
    ...

def parse(cls: BaseParse) -> response_handler:
    """Декоратор для интеграции с uplink."""
    h = response_handler(cls.__call__, requires_consumer=True)
    return h
