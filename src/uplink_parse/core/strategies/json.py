from typing import Any, Literal

from uplink_parse.core.strategies.strategy import Strategy

JSONResult = dict[str, Any]


class JSONStrategy(Strategy[JSONResult, Literal["json"]]):
    pass
