import xml.etree.ElementTree as Tree

from uplink_parse.strategy import Strategy

class XMLStrategy(Strategy):
    def __call__(self, response) -> Tree.Element:
        return Tree.fromstring(response.text)