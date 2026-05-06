from __future__ import annotations

try:
    from bs4 import BeautifulSoup
except ImportError:
    pass

from uplink_parse.core.strategy import Strategy

try:
    import lxml
    features_html = "lxml"
except ImportError:
    features_html = "html.parser"

__all__ = ["HTMLStrategy"]

HTMLResult = "BeautifulSoup"

class HTMLStrategy(Strategy):
    """Strategy for parsing HTML content from HTTP response.

    This strategy converts the response text into a BeautifulSoup object
    for HTML parsing and manipulation. Automatically selects the best
    available parser (lxml if installed, otherwise falls back to
    html.parser).

    The strategy requires BeautifulSoup4 to be installed. If BeautifulSoup
    is not available, an ImportError is raised when calling the strategy.

    Attributes:
        None

    Methods:
        __call__(response): Parses response text and returns BeautifulSoup
                           object.

    Example:
        >>> strategy = HTMLStrategy()
        >>> soup = strategy(response)
        >>> title = soup.find('title').text

    Raises:
        ImportError: If BeautifulSoup is not installed when the strategy
                    is called.
    """

    def __call__(self, response) -> HTMLResult:
        """Parse HTML content from HTTP response into BeautifulSoup object.

        Args:
            response: HTTP response object (similar to requests.Response)
                     containing HTML content to parse.

        Returns:
            BeautifulSoup: Parsed HTML document as BeautifulSoup object.

        Raises:
            ImportError: If BeautifulSoup is not installed. Provides
                        installation instructions via the error message.
        """
        try:
            return BeautifulSoup(response.text, features=features_html)
        except NameError:
            raise ImportError("You need to install `uplink-parse[html]` to use HTMLStrategy or HTMLParse.")