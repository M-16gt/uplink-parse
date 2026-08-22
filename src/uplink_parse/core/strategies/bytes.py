from typing import Literal

from src.uplink_parse.core.strategies.strategy import Strategy

BytesResult = bytes


class BytesStrategy(Strategy[BytesResult, Literal["read", "content", "data", "body"]]):
    pass
