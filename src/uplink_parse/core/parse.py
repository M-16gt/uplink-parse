from __future__ import annotations

from typing import Callable, Self

from uplink_parse.strategies import HTMLStrategy, HTMLResult, TextStrategy, TextResult, XMLStrategy, JSONStrategy, \
    BytesStrategy, BytesResult, JSONResult, XMLResult

try:
    from uplink import response_handler
except ImportError:
    response_handler = lambda handler, requires_consumer=False: handler

__all__ = ("HTMLParse", "XMLParse", "TextParse", "JSONParse", "BytesParse", "BaseParse")


from uplink_parse.core.singleton import Singleton
from uplink_parse.core.processor import extract
from uplink_parse.core._generics import ParseGeneric, strategy, strategy_rt
from uplink_parse.core.ctx import ctx, ScraperCtx

class _ParseObj(ParseGeneric[strategy, strategy_rt], Singleton):

    @property
    def s(self) -> Self:
        return ctx.s

    @property
    def scraper(self) -> Self:
        return ctx.scraper

    @property
    def response(self) -> strategy_rt:
        return ctx.response

    @property
    def r(self) -> strategy_rt:
        return ctx.r

    @property
    def consumer(self):
        return ctx.consumer

    @property
    def c(self):
        return ctx.c

class BaseParse(_ParseObj[strategy, strategy_rt]):
    def __new__(cls, *, is_decorator: bool = True, _for_extract_dict: dict | None = None) -> response_handler | BaseParse:
        instance = super().__new__(cls)
        instance.__extract_dict = _for_extract_dict or {"check_mro": True}
        return instance if not is_decorator else parse(instance)

    def __call__(self, *args, **kwargs):
        response = args[-1]
        response = self.parse_response(response) if self.use_parse_response(response) else response
        consumer = args[0] if len(args) > 1 else None
        with ScraperCtx(response=response, consumer=consumer, scraper=self) as _:
            return self.get_model()(**extract(self, {}))

    @classmethod
    def parse_response(cls, response) -> strategy_rt:
        return cls.config_types["strategy"]()(response)

    @staticmethod
    def use_parse_response(response) -> bool:
        return bool(getattr(response, "status_code", None))

    @staticmethod
    def get_model() -> Callable:
        return lambda **kwargs: kwargs

class HTMLParse(BaseParse[HTMLStrategy, HTMLResult]):
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
    return response_handler(cls, requires_consumer=True)
