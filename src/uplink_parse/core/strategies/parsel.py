from typing import Any, Literal, TypeAlias

from parsel import Selector

from uplink_parse.core.strategies.strategy import Strategy

ParselResult: TypeAlias = Selector


class ParselStrategy(Strategy[ParselResult, Literal["text"]]):
    def transform(self, raw: str, **params: Any) -> ParselResult:
        return Selector(text=raw, **params)
