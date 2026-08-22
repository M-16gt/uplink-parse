from typing import Literal, TypeAlias

from bs4 import BeautifulSoup

from src.uplink_parse.core.strategies.strategy import Strategy

BS4Result: TypeAlias = BeautifulSoup


class BS4Strategy(Strategy[BS4Result, Literal["text"]]):
    def transform(self, raw: str) -> BS4Result:
        return BeautifulSoup(raw, "lxml")
