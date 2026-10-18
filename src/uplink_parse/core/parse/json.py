from uplink_parse.core.parse.base import BaseParse
from uplink_parse.core.strategies.json import JSONResult, JSONStrategy


class JSONParse(BaseParse[JSONStrategy, JSONResult]): ...
