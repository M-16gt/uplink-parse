from abc import abstractmethod
from typing import Any

from uplink_parse.core.singleton import SingletonABC


class Strategy(SingletonABC):
    """Abstract base class for HTTP response parsing strategies.

    Defines the interface for all concrete strategy classes that transform
    a raw HTTP response (similar to requests.Response object) into a specific
    data format (e.g., JSON, HTML, XML, etc.).

    Subclasses must implement the __call__ method which takes a response
    object and returns parsed data of arbitrary type.

    Attributes:
        None

    Methods:
        __call__(response): Abstract method called when applying the strategy
                           to a response.

    Example:
        >>> class JSONStrategy(Strategy):
        ...     def __call__(self, response) -> dict:
        ...         return response.json()
    """

    @abstractmethod
    def __call__(self, response) -> Any:
        """Apply the strategy to an HTTP response.

        Args:
            response: HTTP response object (similar to requests.Response)
                     containing raw data to be parsed.

        Returns:
            Any: Parsed data in the format defined by the concrete strategy
                (e.g., dict for JSON, BeautifulSoup for HTML, etc.).

        Raises:
            NotImplementedError: If the method is not overridden by a subclass.
        """
        pass