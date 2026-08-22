from typing import Literal, TypeAlias

from parsel import Selector

from src.uplink_parse.core.strategies.strategy import Strategy

ParselResult: TypeAlias = Selector


class ParselStrategy(Strategy[ParselResult, Literal["text"]]):
    def transform(self, raw: str) -> ParselResult:
        return Selector(text=raw)
