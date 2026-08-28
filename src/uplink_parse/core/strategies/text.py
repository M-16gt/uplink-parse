from typing import Literal

from uplink_parse.core.strategies.strategy import Strategy

TextResult = str


class TextStrategy(Strategy[TextResult, Literal["text"]]):
    pass
