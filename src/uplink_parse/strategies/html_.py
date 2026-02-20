from __future__ import annotations

try:
    from bs4 import BeautifulSoup
except ImportError: pass

from uplink_parse.strategy import Strategy

try:
    import lxml
    features_html = "lxml"
except ImportError:
    features_html = "html.parser"

__all__ = ["HTMLStrategy"]

class HTMLStrategy(Strategy):

    def __call__(self, response) -> "BeautifulSoup":
        try:
            return BeautifulSoup(response.text, features=features_html)
        except NameError:
            raise ImportError("You need to install `uplink-parse[html]` to use HTMLStrategy or HTMLParse.")