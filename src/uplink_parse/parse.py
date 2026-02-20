from __future__ import annotations

from typing import Callable, Union, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    import xml.etree.ElementTree as Tree

from uplink_parse._collector import PropertyCollector, CombinedMeta

from uplink_parse.utils import strategies, get_strategy_from_content_type


__all__ = ("HTMLParse", "XMLParse", "TextParse", "JSONParse", "BytesParse", "BaseParse", "AutoParse")

class BaseParse(PropertyCollector, ABC, metaclass=CombinedMeta):
    scraper = None
    get_properties = None  # type: ignore

    def __new__(cls, response):
        instance = super().__new__(cls)

        instance.response = instance.parse_response(response) if instance.use_parse_response(response) else response

        return instance.get_dataclass()(**instance.get_properties())

    @staticmethod
    @abstractmethod
    def parse_response(response) -> Union[str, bytes, dict, Tree.Element, "BeautifulSoup"]:
        pass

    @staticmethod
    def use_parse_response(response) -> bool:
        return hasattr(response, "status_code")

    @staticmethod
    def get_dataclass() -> Callable:
        return lambda **kwargs: kwargs

class AutoParse(BaseParse):
    @staticmethod
    def parse_response(response) -> Union[str, bytes, dict, Tree.Element, "BeautifulSoup"]:
        return get_strategy_from_content_type(response.headers["content-type"])(response)

class HTMLParse(BaseParse):
    @staticmethod
    def parse_response(response) -> "BeautifulSoup":
        return strategies["html"](response)


class XMLParse(BaseParse):
    @staticmethod
    def parse_response(response) -> Tree.Element:
        return strategies["xml"](response)


class JSONParse(BaseParse):
    @staticmethod
    def parse_response(response) -> dict:
        return strategies["json"](response)


class TextParse(BaseParse):
    @staticmethod
    def parse_response(response) -> str:
        return strategies["text"](response)


class BytesParse(BaseParse):
    @staticmethod
    def parse_response(response) -> bytes:
        return strategies["bytes"](response)

