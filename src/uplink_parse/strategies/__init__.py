from .bytes import BytesStrategy, BytesResult
from .json_ import JSONStrategy, JSONResult
from .html_ import HTMLStrategy, HTMLResult
from .text_ import TextStrategy, TextResult
from .xml_ import XMLStrategy, XMLResult

__all__ = ["BytesStrategy", "JSONStrategy", "HTMLStrategy", "TextStrategy", "XMLStrategy", "BytesResult", "JSONResult",
           "HTMLResult", "TextResult", "XMLResult"]
