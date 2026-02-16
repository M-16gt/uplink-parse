from typing import Callable

from bs4 import BeautifulSoup

from ._collector import PropertyCollector

from .converts import strategies

class BaseParse(PropertyCollector):

    def __new__(cls, response):
        instance = super().__new__(cls)

        instance.response = instance.convert_response(response) if instance.use_convert(response) else response

        return instance.get_dataclass()(**instance.get_properties())

    @staticmethod
    def convert_response(response) -> BeautifulSoup:
        return strategies["html"](response)

    @staticmethod
    def use_convert(response) -> bool:
        return hasattr(response, "status_code")

    @staticmethod
    def get_dataclass() -> Callable:
        return lambda **kwargs: kwargs