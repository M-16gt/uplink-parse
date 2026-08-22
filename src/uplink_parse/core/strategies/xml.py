from typing import Any, Literal
from xml.etree import ElementTree as ET

from src.uplink_parse.core.strategies.strategy import Strategy

XMLResult = ET.Element


class XMLStrategy(Strategy[XMLResult, Literal["text"]]):
    def transform(self, raw: str, **params: Any) -> ET.Element:
        return ET.fromstring(raw)
