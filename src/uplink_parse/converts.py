from bs4 import BeautifulSoup

try:
    import lxml
    features_html = "lxml"
except ImportError:
    features_html = "html.parser"

class Strategy:

    def __call__(self, response):
        raise NotImplementedError

class HTMLStrategy(Strategy):

    def __call__(self, response):
        return BeautifulSoup(response.text, features=features_html)

class JSONStrategy(Strategy):
    def __call__(self, response):

        return response.json()

def _get_strategies() -> dict[str, object]:
    dict_ = {}
    for subclass in Strategy.__subclasses__():
        dict_[subclass.__name__.lower().removesuffix("strategy")] = subclass()

    return dict_

strategies = _get_strategies()


