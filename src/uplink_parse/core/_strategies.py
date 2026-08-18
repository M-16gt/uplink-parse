import xml.etree.ElementTree as ET # noqa
from typing import Coroutine, TYPE_CHECKING

from uplink_parse.core.utils import _to_awaitable

if TYPE_CHECKING:
    from bs4 import BeautifulSoup

from uplink_parse.core.strategy import Strategy

TextResult = str


class TextStrategy(Strategy[TextResult | Coroutine]):
    funcs_dict = {
        "RequestsClient": lambda response: response.text,
        "AiohttpClient": lambda response: response.text()
    }


JSONResult = dict


class JSONStrategy(Strategy[JSONResult | Coroutine]):
    funcs_dict = {
        "RequestsClient": lambda response: response.json(),
        "AiohttpClient": lambda response: response.json()
    }


BytesResult = bytes


class BytesStrategy(Strategy[BytesResult]):
    funcs_dict = {
        "RequestsClient": lambda response: response.content,
        "AiohttpClient": lambda response: response.read()
    }

XMLResult = ET.Element

async def _async_tree(response) -> XMLResult:
    return ET.fromstring(await TextStrategy()(response))


class XMLStrategy(Strategy[XMLResult | Coroutine]):
    funcs_dict = {
        "RequestsClient": lambda response: ET.fromstring(response.text),
        "AiohttpClient": _async_tree
    }

BS4Result = "BeautifulSoup"


def _sync_bs4(response) -> "BeautifulSoup":
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        raise ImportError("beautifulsoup4 is not installed. Run: pip install beautifulsoup4")
    return BeautifulSoup(TextStrategy()(response), "html.parser")


async def _async_soup(response) -> "BeautifulSoup":
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        raise ImportError("beautifulsoup4 is not installed. Run: pip install beautifulsoup4")

    return BeautifulSoup(await _to_awaitable(TextStrategy()(response)), "html.parser")


class BS4Strategy(Strategy[BS4Result | Coroutine]):
    funcs_dict = {
        "RequestsClient": _sync_bs4,
        "AiohttpClient": _async_soup
    }