from uplink_parse.core.parse.base import BaseParse
from uplink_parse.core.strategies.xml import XMLResult, XMLStrategy


class XMLParse(BaseParse[XMLStrategy, XMLResult]): ...
