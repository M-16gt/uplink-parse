from uplink_parse.core.parse.base import BaseParse
from uplink_parse.core.strategies.text import TextResult, TextStrategy


class TextParse(BaseParse[TextStrategy, TextResult]): ...
