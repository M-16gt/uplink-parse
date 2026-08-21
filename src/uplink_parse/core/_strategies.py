from __future__ import annotations

from typing import Any, Literal, TypeAlias
from xml.etree import ElementTree as ET

from src.uplink_parse.core.strategy import Strategy

TextResult = str


class TextStrategy(Strategy[TextResult, Literal["text"]]):
    pass


JSONResult: TypeAlias = dict[str, Any]


class JSONStrategy(Strategy[JSONResult, Literal["json"]]):
    pass


BytesResult = bytes


class BytesStrategy(Strategy[BytesResult, Literal["read", "content", "data", "body"]]):
    pass


XMLResult = ET.Element


class XMLStrategy(Strategy[XMLResult, Literal["text"]]):
    def transform(self, raw: str) -> ET.Element:
        return ET.fromstring(raw)


BS4Result: TypeAlias = "BeautifulSoup"  # type: ignore[name-defined]  # noqa: F821


class BS4Strategy(Strategy[BS4Result, Literal["text"]]):
    def transform(self, raw: str) -> Any:
        from bs4 import BeautifulSoup

        return BeautifulSoup(raw, "html.parser")


ParselResult: TypeAlias = "Selector"  # type: ignore[name-defined]  # noqa: F821


class ParselStrategy(Strategy[ParselResult, Literal["text"]]):
    def transform(self, raw: str) -> Any:
        from parsel import Selector

        return Selector(text=raw)
